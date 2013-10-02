import streamcorpus.pipeline.stages

from ._factorie import factorie_batch

def setup():
    streamcorpus.pipeline.stages.register_stage('factorie_batch', factorie_batch)
