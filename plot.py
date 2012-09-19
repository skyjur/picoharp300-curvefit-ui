# encoding: utf-8
import sys
import picoharp
import matplotlib.pyplot as plt

# Atidarom .phd failą skaitymui:
data = picoharp.PicoharpParser(sys.argv[1])
# Gaunam pirmos kreivės reikšmes:
res1, curve1 = data.get_curve(0)
# Gaunam antros kreivės reikšmes:
res2, curve2 = data.get_curve(1)

# res1, ir res2 reiškia kreivės intervalą (== 0.0016 sec)

# Paruošiam plotą ant kurio paišyti kreives:
fig = plt.figure()
ax = fig.add_subplot(1,1,1)

# Paišom abi kreives:
ax.plot(curve1, 'r.', curve2, 'b.')

# Nustatom logaritminę skalę:
ax.set_yscale('log')

# Rodom interface:
plt.show()
