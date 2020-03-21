
from .SmartTabs import t

expected = '''
Column 1 Header Col2 Col3
Shorter 1       Col2 Col3
Longer message on column 1 Col2 Col3
Again shorter 1            Col2 Col3
Longer message on column 1 Col2 Col3
Something in between       Col2 Col3
Something in between v2    I didn't move ! But now I did
Something in between v10   shorter         Now I didn't move either
Everything in between      from now on     will be aligned
Until you call             t.reset()
like this, see ?
test 1     test 2
test 10    test 20
Use it with unknown length variables like this:
Sending request to: example.com and waiting for reply on 123
Sending request to: linux.org   and waiting for reply on 123
Sending request to: superlongurl.long.tld.too and waiting for reply on 123
Sending request to: wikipedia.com             and waiting for reply on 123
Sending request to: notsolongurl.tld          and waiting for reply on 123
Sending request to: github.com                and waiting for reply on 123
Sending request to: git-scm.com               and waiting for reply on 123
You can also        avoid modifying the existing layout by calling t.over() instead of t().
'''

def test():

    global expected

    line = '\n'
    line += t('Column 1 Header\t Col2\t Col3') + '\n'
    line += t('Shorter 1\t Col2\t Col3') + '\n'
    line += t('Longer message on column 1\t Col2\t Col3') + '\n'
    line += t('Again shorter 1\t Col2\t Col3') + '\n'
    line += t('Longer message on column 1\t Col2\t Col3') + '\n'
    line += t('Something in between\t Col2\t Col3') + '\n'
    line += t('Something in between v2\t I didn\'t move !\t But now I did') + '\n'
    line += t('Something in between v10\t shorter\t Now I didn\'t move either') + '\n'
    line += t('Everything in between\t from now on\t will be aligned') + '\n'
    line += t('Until you call\t t.reset()') + '\n'
    t.reset()
    line += t('like this,\t see ?') + '\n'
    line += t('test 1\t test 2') + '\n'
    line += t('test 10\t test 20') + '\n'
    line += 'Use it with unknown length variables like this:' + '\n'
    for url in ['example.com', 'linux.org', 'superlongurl.long.tld.too', 'wikipedia.com', 'notsolongurl.tld', 'github.com', 'git-scm.com']:
        line += t('Sending request to:\t {0}\t and waiting for reply on {1}'.format(url, 123)) + '\n'
    line += t.over('You can also\t avoid modifying the existing layout by calling t.over() instead of t().') + '\n'

    assert line == expected

