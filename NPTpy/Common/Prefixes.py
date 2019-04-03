
prefixesIEC = ['  ','Ki','Mi','Gi','Ti','Pi','Ei','Zi','Yi']
prefixesISO = [' ' ,'K' ,'M' ,'G' ,'T' ,'P' ,'E' ,'Z' ,'Y' ]

def prefixIEC(number):
    for i in range(len(prefixesIEC) - 1):
        if abs(number) < 1024:
            break
        number //= 1024
    return '{0:4d}{1}'.format(number, prefixesIEC[i])

def prefixISO(number):
    for i in range(len(prefixesISO) - 1):
        if abs(number) < 1000.0:
            break
        number /= 1000.0
    return '{0:5.1f}{1}'.format(number, prefixesISO[i])
