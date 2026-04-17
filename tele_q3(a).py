def find_high_yield(x,tele_data): #function to find the highest energy yield
    r = None
    mx = -1
    tele_dict = {}

    for i in tele_data: #making the dictionary
        tele_dict[i[0]] = i[1:]

    for i in range(len(x)):
        q = 0
        if x[i] in tele_dict: #O(1)
            q = tele_dict[x[i]][0]*tele_dict[x[i]][1]*0.966
        if q>mx:
            mx = q
            r = x[i]
    
    return r #returning the value of r(best value for highest energy yeild)

