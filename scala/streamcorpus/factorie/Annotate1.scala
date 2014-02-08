package streamcorpus.factorie

import java.io.{FileOutputStream, FileInputStream}
import org.apache.thrift.protocol.TBinaryProtocol
import org.apache.thrift.transport.{TTransportException, TIOStreamTransport, TTransport}
import streamcorpus.StreamItem
import streamcorpus._
import java.io.{FileOutputStream, FileInputStream}
import java.nio.ByteBuffer

import cc.factorie.app.nlp.mention.{Mention,MentionList,MentionType}

object Annotate1 {
  
  // Maps from FACTORIE category name strings to StreamCorpus constants
  val entityTypeMap = scala.collection.Map("PER" -> EntityType.Per, "LOC" -> EntityType.Loc, "ORG" -> EntityType.Org, "MISC" -> EntityType.Misc)
  val mentionTypeMap = scala.collection.Map("NAM" -> MentionType.Name, "NOM" -> MentionType.Nom, "PRO" -> MentionType.Pro)
  
  def main(args: Array[String]) {
    val verbose: Boolean = args.contains("--verbose")
    
    //val i_transport: TTransport = new TIOStreamTransport(new FileInputStream("../test-data/john-smith-tagged-by-lingpipe-0-v0_3_0.sc"))
    //val o_transport: TTransport = new TIOStreamTransport(new FileOutputStream("/tmp/john-smith-tagged-by-factorie-0-v0_3_0.sc"))
    val i_transport: TTransport = new TIOStreamTransport(new FileInputStream(args(0)))
    val o_transport: TTransport = new TIOStreamTransport(new FileOutputStream(args(1)))
    val i_binProto: TBinaryProtocol = new TBinaryProtocol(i_transport)
    val o_binProto: TBinaryProtocol = new TBinaryProtocol(o_transport)
    i_transport.open()
    
    while (true) {
      try {
        val item: StreamItem = StreamItem.decode(i_binProto)
        item.body match {
          case Some(contentItem) => {
            println(item.docId)
            val tag: String = "factorie"
            val newTaggings = Tagging(
                taggerId = tag,
                rawTagging = ByteBuffer.wrap(Array[Byte]()), // serialized tagging data in some "native" format, such as XML or JSON // TODO Do I need to put something here?
                taggerConfig = Some("Tokenizer1,SentenceSegmenter1,POS1"),
                taggerVersion = Some("1.0"),
                generationTime = Some(StreamTime(zuluTimestamp = "1970-01-01T00:00:01.000000Z", epochTicks = 1)) // TODO What is this supposed to be?
              )
            
            // Create a new FACTORIE document with contents equal to the document String
            val doc = new cc.factorie.app.nlp.Document(contentItem.cleanVisible.get)
            val pipeline = cc.factorie.app.nlp.DocumentAnnotatorPipeline(cc.factorie.app.nlp.lemma.WordNetLemmatizer, cc.factorie.app.nlp.pos.POS1, cc.factorie.app.nlp.ner.NER1, cc.factorie.app.nlp.coref.WithinDocCoref1Ner, cc.factorie.app.nlp.parse.DepParser1)
            pipeline.process(doc)
            // Optionally print a trace of what we are doing
            if (verbose) println(doc.owplString(pipeline))
                        
            // Translate FACTORIE data/tags to streamcorpus format
            var mentionId = 0
            val newSentences = for (sentence <- doc.sentences.toSeq) yield {
              Sentence(tokens = for (token <- sentence.tokens.toSeq) yield {
                val posLabel = token.posLabel
                val nerLabel = token.attr[cc.factorie.app.nlp.ner.BilouConllNerLabel]
                val mention:Mention = doc.attr[MentionList].filter(mention => mention.span.contains(token)) match { case ms:Seq[Mention] if ms.length > 0 => ms.head; case _ => null }
                val mentionId:Int = if (mention eq null) -1 else doc.attr[MentionList].indexOf(mention)
                val mentionCategory:String = if (mention ne null) mention.attr[MentionType].categoryValue else "O"
                val corefMap = token.document.attr[cc.factorie.util.coref.GenericEntityMap[Mention]]
                val equivId:Long = if (mention ne null) corefMap.getEntity(mention) else -1
                Token(token.positionInSentence, token.string,
                      sentencePos = token.positionInSentence,
                      lemma = Some(token.lemmaString),
                      pos = Some(posLabel.categoryValue),
                      entityType = if (nerLabel.intValue == 0) None else Some(entityTypeMap(nerLabel.categoryValue.drop(2))),
                      mentionType = if (mentionCategory == "O") None else Some(mentionTypeMap(mentionCategory)),
                      mentionId = mentionId,
                      parentId = token.parseParentIndex,
                      dependencyPath = Some(token.parseLabel.categoryValue),
                      equivId = equivId.toInt,
                      // offsets allow alignment of output from multiple taggers or other metadata referring to parts of a document.
                      // TODO: get the firstByte/lengthBytes and firstChar/lengthChars from FACTORIE output.
                      // Ideally, both Bytes and Chars would be available
                      //offsets = Map(
                      //              OffsetType.Bytes -> Offset(OffsetType.Bytes, token.firstByte, token.lengthChars),
                      //              OffsetType.Chars -> Offset(OffsetType.Chars, token.firstChar, token.lengthChars)
                      //              )
                      )
                }
              )
            }
                        
            val newItem = item.copy(body = Some(contentItem.copy(
              taggings = contentItem.taggings + (tag -> newTaggings),
              sentences = contentItem.sentences + (tag -> newSentences)
            )))

            // Write out the new annotations
            newItem.write(o_binProto)
            //item.write(o_binProto) // TODO Remove this
            o_transport.flush()
            
          }
          case _ => println("Bad StreamItem: "+item)
        }
        println("--------------------------------------------")
      } catch {
        case te: TTransportException => if (te.getType == TTransportException.END_OF_FILE) {
          println("END")
          return
        } else { 
          println("type " + te.getType)
          throw te
        }
      }
    }
  }
}
