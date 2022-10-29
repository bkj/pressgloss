# Standard imports
import json
import os
from collections import Counter
import copy

# pressgloss imports
import pressgloss.core as PRESSGLOSS
from . import helpers

def prettifygamefile(inpath, outpath): # type: (str, str) -> None
  """
  Reads a JSON game log file and writes it prettily to another file

  :param inpath: the location on disk of the JSON game log
  :type inpath: str
  :param outpath: the location on disk to write the pretty JSON game log
  :type outpath: str

  """

  with open(inpath, 'r', encoding='UTF-8') as jf:
    curgame = json.load(jf)

  with open(outpath, 'w', encoding='UTF-8') as of:
    json.dump(curgame, of, indent=2)

def operatorcounts(incontent): # type: (PRESSGLOSS.PressMessage) -> Counter
  """
  Counts the uses of each DAIDE operator in the message.

  :param incontent: the DAIDE message
  :type incontent PRESSGLOSS.PressMessage

  :return: how many times each DAIDE operator was used in the message
  :rtype: Counter

  """

  retct = Counter()
  retct[incontent.operator] += 1
  if incontent.details is not None:
    retct += operatorcounts(incontent.details)

  return retct

def annotatelog(inlog): # type: ({}) -> {}
  """
  Annotate a Diplomacy game log with glosses for each message containing only DAIDE

  :param inlog: the parsed-from-JSON representation of a Diplomacy game log
  :type inlog: {}

  :return: the same game log with press which was DAIDE annotated with English glosses.
  :rtype: {}

  """

  retdict = copy.deepcopy(inlog)

  if 'phases' in retdict:
    retdict['id'] += '_gloss'
    for curphase in retdict['phases']:
      if 'messages' in curphase:
        for curmessage in curphase['messages']:
          cursender = curmessage['sender']
          cursendersym = helpers.powername2sym[cursender]
          currecipient = curmessage['recipient']
          currecsym = helpers.powername2sym[currecipient]
          if currecipient != 'GLOBAL':
            curcontent = curmessage['message']
            curdaide = 'FRM (' + cursendersym + ') (' + currecsym + ') (' + curcontent + ')'
            curutterance = PRESSGLOSS.PressUtterance(curdaide, ['Objective', 'Expert'])
            curutterance.formenglish()
            curpress = curutterance.english
            if 'Ahem' in curpress:
              curmessage['message'] = curcontent + ':\nNot glossable DAIDE.'
            else:
              curpress = curpress.replace('<ul>', '\n')
              curpress = curpress.replace('</ul>', '')
              curpress = curpress.replace('<li>', '* ')
              curpress = curpress.replace('</li>', '\n')
              curpress = curpress.replace('<br>', '\n')
              curpress = curpress.replace('<br/>', '\n')
              curmessage['message'] = curcontent + ':\n' + curpress
          else:
            curmessage['message'] += ':\nGlobal messages not glossed.'

  return retdict

def analyzegym(inpath): # type: (str) -> []
  """
  Searches through a folder for game logs and returns a list of paths to those which might be interesting for analysis.
  Also creates prettyfied JSON logs and game transcripts with press gloss

  :param inpath: the folder that the logs are in
  :type inpath: str

  :return: a list of paths to game log files used in the analysis
  :rtype: []

  """

  retset = set()

  for root, dirs, files in os.walk(os.path.abspath(inpath)):
    for file in files:
      curfullpath = os.path.join(root, file)
      if file.endswith('.json') and '_pretty.json' not in file and '_gloss.json' not in file:
        with open(curfullpath, 'r', encoding='UTF-8') as jf:
          curgame = json.load(jf)
        if 'phases' in curgame:
          daideoperators = Counter()
          powerdaideuse = {'FRANCE': Counter(),
                           'ENGLAND': Counter(),
                           'AUSTRIA': Counter(),
                           'GERMANY': Counter(),
                           'ITALY': Counter(),
                           'RUSSIA': Counter(),
                           'TURKEY': Counter()}
          messagesenders = Counter()
          messagerecipients = Counter()
          messageexchanges = Counter()
          messages = 0
          daideerrors = 0
          retset.add(curfullpath)
          prtyfile = file.replace('.json', '_pretty.json')
          fullprettypath = os.path.join(root, prtyfile)
          prettifygamefile(curfullpath, fullprettypath)
          for curphase in curgame['phases']:
            if 'messages' in curphase:
              for curmessage in curphase['messages']:
                messages += 1
                cursender = curmessage['sender']
                messagesenders[cursender] += 1
                cursendersym = helpers.powername2sym[cursender]
                currecipient = curmessage['recipient']
                messagerecipients[currecipient] += 1
                currecsym = helpers.powername2sym[currecipient]
                messageexchanges[cursender + '->' + currecipient] += 1
                if currecipient != 'GLOBAL':
                  curcontent = curmessage['message']
                  curdaide = 'FRM (' + cursendersym + ') (' + currecsym + ') (' + curcontent + ')'
                  curutterance = PRESSGLOSS.PressUtterance(curdaide, ['Objective', 'Expert'])
                  daideoperators += operatorcounts(curutterance.content)
                  powerdaideuse[cursender] += operatorcounts(curutterance.content)
                  curutterance.formenglish()
                  curpress = curutterance.english
                  if 'Ahem' in curpress:
                    daideerrors += 1
                    powerdaideuse[cursender]['Error'] += 1
          curglossgame = annotatelog(curgame)
          glossfile = file.replace('.json', '_gloss.json')
          fullglosspath = os.path.join(root, glossfile)
          with open(fullglosspath, 'w', encoding='UTF-8') as of:
            json.dump(curglossgame, of, indent=2)
          print(curfullpath)
          print('  ' + str(messages) + ' messages sent')
          print('  ' + str(daideerrors) + ' DAIDE errors')
          print('  Messages sent by ' + str(messagesenders.most_common()))
          print('  Messages sent to ' + str(messagerecipients.most_common()))
          print('  Message pairs ' +  str(messageexchanges.most_common()))
          print('  DAIDE usage ' +  str(daideoperators.most_common()))
          for curpower, curdaideuse in powerdaideuse.items():
            print('  ' + curpower + ' DAIDE usage ' + str(curdaideuse.most_common()))

  return list(retset)

def analyzebackup(inpath): # type: (str) -> []
  """
  Searches through a folder for game logs and returns a list of paths to those which might be interesting for analysis.

  :param inpath: the folder that the logs are in
  :type inpath: str

  """

  retset = set()
  tonesused = Counter()
  daideoperators = Counter()
  messages = 0
  daideerrors = 0

  for root, dirs, files in os.walk(os.path.abspath(inpath)):
    for file in files:
      curfullpath = os.path.join(root, file)
      if file.endswith('.json'):
        with open(curfullpath, 'r', encoding='UTF-8') as jf:
          curgame = json.load(jf)
        if 'message_history' in curgame:
          for curkey, messagelist in curgame['message_history'].items():
            for curmessage in messagelist:
              curtonesstr = curmessage['tones']
              if curtonesstr == '':
                curtonesstr = 'Objective'
              curtones = curtonesstr.split(',')
              for curtone in curtones:
                tonesused[curtone] += 1
              curdaide = PRESSGLOSS.PressUtterance(curmessage['daide'], curtones)
              messages += 1
              if 'Ahem' in curdaide.english:
                daideerrors += 1
              if curdaide.content is not None:
                daideoperators[curdaide.content.operator] += 1
                if curdaide.content.details is not None:
                  daideoperators[curdaide.content.details.operator] += 1
            if len(messagelist) > 0 and curfullpath not in retset:
              retset.add(curfullpath)
        if 'status' in curgame and curgame['status'] == 'completed':
          print(curfullpath + ' completed')
          print('  won by ' + str(curgame['victory']))
          print('  outcome: ' + str(curgame['outcome']))
        else:
          print(curfullpath + ' in progress')
        ctrl2powers = {}
        for curpower, powerinfo in curgame['powers'].items():
          print(curpower + ':')
          dummyct = 0
          for ctrlid, ctrlname in powerinfo['controller'].items():
            cleanname = ctrlname.strip().lower()
            if cleanname == 'dummy':
              dummyct += 1
            if cleanname not in ctrl2powers:
              ctrl2powers[cleanname] = set()
            ctrl2powers[cleanname].add(curpower)
          if len(powerinfo['controller']) == dummyct and dummyct > 0:
            print('  Dummy')
          elif dummyct > 0:
            print('  Hybrid')
          elif dummyct == 0:
            print('  All Human')
          else:
            print('  Odd controller data')
        print(str(ctrl2powers))
        print('  ' + str(len(curgame['order_history'])) + ' seasons played')

  print('Press found in ' + str(len(retset)) + ' games.')
  print('  ' + str(messages) + ' messages found.')
  print('  ' + str(daideerrors) + ' DAIDE errors found.')
  print(str(tonesused.most_common()))
  print(str(daideoperators.most_common()))

  return list(retset)
