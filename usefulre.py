        n = env['note']
        n = re.sub('<elog:exper=(.*)/(.*)>', '@elog:\\1=\\2@', n)
        n = re.sub('<elog:dfile=(.*)/(.*)>', '@elog:\\1=\\2@', n)
        n = re.sub('<elog:attach=(.*)>',   '@elog:\\1=\\2@', n)
        n = cgi.escape(n)
        n = re.sub('@elog:exper=(.*)/(.*)>', '<@elog:\\1=\\2@', n)
        n = re.sub('@elog:dfile=(.*)/(.*)>', '@elog:\\1=\\2@', n)
        n = re.sub('@elog:attach=(.*)>',   '@elog:\\1=\\2@', n)
        env['note'] = n.replace("\n", "<br>\n")

