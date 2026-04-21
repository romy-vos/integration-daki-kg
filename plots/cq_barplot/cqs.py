import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

rq = pd.read_csv("RCQ.txt", sep = "\t")
cq = pd.read_csv("CCQ.txt", sep = "\t")

rq['index'] = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
rq['total_practice'] = rq['total GS'] - rq['total OOS']
cq['index'] = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
cq['total_practice'] = cq['total GS'] - cq['total OOS']

df = cq.copy()
df2 = rq.copy()

plt.style.use('seaborn-v0_8-white') # or 'ggplot' if you prefer
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

# PLOT 1
df.plot(kind='bar', x='index', y='total GS',
color='#E0E0E0', width=0.9, label='Golden standard', legend=False, ax=ax1)

df.plot(kind='bar', x='index', y='total_practice',
color='#9E9E9E', width=0.7, label='In scope', ax=ax1, legend=False)

df.plot(kind='bar', x='index', y=['v0', 'v1', 'v2'],
color=['#4A90E2', '#F5A623', '#7ED321'],
width=0.5, ax=ax1, edgecolor='white', linewidth=0.5, legend = False)

ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_color('#CCCCCC')
ax1.spines['bottom'].set_color('#CCCCCC')
ax1.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=.2)
ax1.set_title('a. Clinical CQ', fontsize=14, pad=20, fontweight = "bold")
ax1.set_xlabel('CQ number', fontsize=12, labelpad=10)
ax1.set_ylabel('Correct Answers', fontsize=12, labelpad=10)
ax1.tick_params(axis='x', rotation=0)


# PLOT 2
df2.plot(kind='bar', x='index', y='total GS',
color='#E0E0E0', width=0.9, label='Golden standard', legend=False, ax=ax2)

df2.plot(kind='bar', x='index', y='total_practice',
color='#9E9E9E', width=0.7, label='In scope', ax=ax2, legend=False)

df2.plot(kind='bar', x='index', y=['v0', 'v1', 'v2'], color=['#4A90E2', '#F5A623', '#7ED321'],
width=0.5, ax=ax2, edgecolor='white', linewidth=0.5, legend = False)

ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['left'].set_color('#CCCCCC')
ax2.spines['bottom'].set_color('#CCCCCC')
ax2.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=.2)
ax2.set_title('b. Research CQ', fontsize=14, pad=20, fontweight = "bold")
ax2.set_xlabel('CQ number', fontsize=12, labelpad=10)
ax2.tick_params(axis='x', rotation=0)
ax2.legend(bbox_to_anchor=(0.55, 1), loc='upper left', frameon=True)

plt.savefig("CQperformance.pdf")