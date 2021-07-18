import sqlite3
# %matplotlib notebook
import matplotlib.pyplot as plt
import numpy as np

dbconn = sqlite3.connect('main.db')
dbconn.row_factory = sqlite3.Row

cursor = dbconn.execute("SELECT * FROM users")
for row in cursor:
    print(row["total"])

cursor = dbconn.execute("SELECT * FROM users")
scores = [row["total"] for row in cursor]

fig, ax = plt.subplots()
# ax.plot((np.log(np.log(np.log(np.abs(scores))))*np.sign(scores)-0.46)*2500+140.66)
ax.plot(scores)
ax.grid()

cursor = dbconn.execute("SELECT * FROM users")
for row in cursor:
    dbconn.execute("UPDATE users SET total = ? WHERE id = ?",
                   ((np.log(np.log(np.log(np.abs(row["total"]))))*np.sign(row["total"])-0.46)*2500+140.66, row["id"]))
dbconn.commit()


