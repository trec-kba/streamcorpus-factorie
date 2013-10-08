#!python

'''
transform chunks using factorie grammar tagger
'''

import glob
import logging
import os
import random
import subprocess
import time

from streamcorpus import Chunk
from streamcorpus_pipeline.config import configure_logger
from streamcorpus_pipeline.stages import BatchTransform


logger = logging.getLogger(__name__)
configure_logger(logger)


class FactorieBase(object):
    def __init__(self, config):
        self.config = config
        self.scala = config.get('scala', 'scala')
        self.libdirs = config.get('libdirs', [])
        self.classpath_tail = config.get('classpath_tail', [])
        self.memory = config.get('memory', '5G')
        self.cwd = config.get('cwd')  # None is okay for subprocess.Popen(cwd=)
        self.process = None

    def call_factorie(self, inpath, outpath):
        if False:
            self.process = subprocess.Popen(
                [os.path.join(self.cwd, 'factorie.sh'), inpath, outpath],
                cwd=self.cwd)
            return
        cp_parts = filter(None, os.environ.get('CLASSPATH', '').split(':'))
        for libdir in self.libdirs:
            #libdir = os.path.abspath(libdir)
            jars = glob.glob(os.path.join(libdir, '*.jar'))
            jars.sort()
            for jar in jars:
                cp_parts.append(jar)
        cp_parts.extend(self.classpath_tail)
        cmd = [self.scala, '-J-Xmx' + self.memory, 'streamcorpus.factorie.Annotate1', inpath, outpath]
        env = {
            'CLASSPATH': ':'.join(cp_parts),
            'PATH': os.environ['PATH'],
            'PWD': self.cwd,
            'LANG': 'en_US.UTF-8',
        }
        logger.debug('starting %r (env=%r, cwd=%r)', cmd, env, self.cwd)
        self.process = subprocess.Popen(cmd, env=env, cwd=self.cwd)

    def shutdown(self):
        if self.process:
            self.process.terminate()
            self.process = None


class factorie(FactorieBase):
    '''
    incremental transform
    '''
    def __init__(self, config):
        super(FactorieIncremetal, self).__init__(config)

        self.toFactoriePipeName = None
        self.fromFactoriePipeName = None
        self.pipeToFactorie = None
        self.pipeFromFactorie = None
        self.taggedChunkIter = None

    def start(self):
        self.toFactoriePipeName = os.tmpnam()
        self.fromFactoriePipeName = os.tmpnam()
        os.mkfifo(self.toFactoriePipeName)
        os.mkfifo(self.fromFactoriePipeName)
        logger.debug('made fifos %r %r', self.toFactoriePipeName, self.fromFactoriePipeName)

        self.call_factorie(self.toFactoriePipeName, self.fromFactoriePipeName)

        self.pipeToFactorie = Chunk(path=self.toFactoriePipeName, mode='ab')
        self.pipeFromFactorie = Chunk(path=self.fromFactoriePipeName, mode='rb')
        self.taggedChunkIter = iter(self.pipeFromFactorie)

    def close(self):
        self.pipeToFactorie.close()
        self.taggedChunkIter = None
        self.pipeFromFactorie = None
        os.unlink(self.toFactoriePipeName)
        os.unlink(self.fromFactoriePipeName)
        if self.process:
            self.process.terminate()
            self.process = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __call__(self, stream_item, context):
        if not self.process:
            self.start()
        logger.debug('pushing stream item to factorie')
        self.pipeToFactorie.add(stream_item)
        self.pipeToFactorie.flush()
        nc = self.taggedChunkIter.next()
        logger.debug('got item from factorie')
        return nc


def _randstr(length):
    return ''.join(['%x' % random.randint(0,15) for z in xrange(length)])


# multiple inheritance is horrible. sorry.
# I want functionality from FactorieBase, and I think I need this class to be tagged as BatchTransform
class factorie_batch(BatchTransform, FactorieBase):
    "Wrapper for factorie language analysis and tagging"

    def __init__(self, config):
        #BatchTransform.__init__(self, config)
        FactorieBase.__init__(self, config)

    def process_path(self, path):
        '''
        run factorie tagger on streamcorpus chunk file at path
        read data from path, write data out to pathB, move pathB to path
        '''
        start = time.time()
        td = os.path.dirname(path)
        tpath = os.path.join(td, _randstr(40))
        self.call_factorie(path, tpath)
        retcode = self.process.wait()
        if retcode != 0:
            msg = 'factorie returned code %d' % (retcode,)
            logger.error(msg)
            if (not self.config.get('keep_temps', False)) and os.path.exists(tpath):
                logger.info('deleting tempfile %s', tpath)
                try:
                    os.unlink(tpath)
                except:
                    logger.warn('failed to delete tempfile %r', tpath, exc_info=True)
                    # but don't care that much, move on
            raise Exception(msg)
        os.rename(tpath, path)
        logger.info('factorie tagging took %0.1f seconds', time.time() - start)

    def shutdown(self):
        FactorieBase.shutdown(self)


def main():
    import argparse
    from streamcorpus.pipeline.config import load_layered_configs

    global logger
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    ap = argparse.ArgumentParser()
    ap.add_argument('--config', dest="configs", action="append", help="config .yaml files, may overlap, later values win")
    ap.add_argument('inpath')
    ap.add_argument('outpath')
    args = ap.parse_args()
    
    config = load_layered_configs(args.configs)
    logging.debug('config: %r', config)
    config = config.get('streamcorpus.pipeline', {}).get('factorie_batch', {})
    logging.debug('factorie config: %r', config)

    factorie = FactorieBase(config)
    factorie.call_factorie(args.inpath, args.outpath)
    retcode = factorie.process.wait()
    if retcode != 0:
        logging.info('factorie retcode = %r', retcode)


if __name__ == '__main__':
    main()
