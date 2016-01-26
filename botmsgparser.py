#from __future__ import absolute_import
from subprocess import call
from dispatcher import MessageDispatcher, Message
from difflib import SequenceMatcher
from six import iteritems
from slackbot.utils import to_utf8, WorkerPool
import logging
import traceback

logger = logging.getLogger(__name__)

def slack_msg_parser(msg):
    #print msg
    if 'text' in msg:
        text = msg['text']
    elif 'attachments' in msg:
        text = msg['attachments'][0]['pretext']
    text = str(text)
    return text


class newMessageDispatcher(MessageDispatcher):
    def __init__(self, slackclient, plugins):
        self._client = slackclient
        self._pool = WorkerPool(self.slack_msg_dispatcher)
        self._plugins = plugins
        
    def test(self):
        print "test in sub class"

    def slack_msg_parser(msg):
        if 'text' in msg:
            text = msg['text']
        elif 'attachments' in msg:
            text = msg['attachments'][0]['pretext']
        text = (str(text)).upper()
        
        return text

    def typo_check(self, str1, str2):
        if str1.isupper() is False:
            str1 = str1.upper()
        if str2.isupper() is False:
            str2 = str2.upper()
        return SequenceMatcher(None, str1, str2).ratio()

    def slack_msg_dispatcher(self,msg):
        category = msg[0]
        msg = msg[1]
        text = slack_msg_parser(msg)
        responded = False
        for func, args in self._plugins.get_plugins(category, text):
            if func:
                responded = True
                try:
                    func(Message(self._client, msg), *args)
                except:
                    logger.exception('failed to handle message %s with plugin "%s"', text, func.__name__)
                    reply = '[%s] I have problem when handling "%s"\n' % (func.__name__, text)
                    reply += '```\n%s\n```' % traceback.format_exc()
                    self._client.rtm_send_message(msg['channel'], reply)
            else:
                print "Let me check if you had a typo... \n"
               # for p, v in iteritems(self._plugins.commands['respond_to']):
                    #print v
                for matcher in self._plugins.commands[category]:
                    #print "matcher: " + "".join(matcher.pattern) + " text: " + "".join(text) 
                    #print "= "                                               
                    #print self. typo_check(matcher.pattern,text)
                    if self.typo_check(matcher.pattern, text) >=0.88:
                        responded = True
                        try:
                            print "I think you actually mean..." + 
                            func(Message(self._client, msg), *args)
                    except:
                        logger.exception('failed to handle message %s with plugin "%s"', text, func.__name__)
                        reply = '[%s] I have problem when handling "%s"\n' % (func.__name__, text)
                        reply += '```\n%s\n```' % traceback.format_exc()
                        self._client.rtm_send_message(msg['channel'], reply)
#                    print r
#                    print "\n"
            if not responded and category == 'respond_to':
                self._default_reply(msg)