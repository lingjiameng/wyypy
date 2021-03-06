import requests
import re
from bs4 import BeautifulSoup
import json
import time
import threading
import os
import pickle

headers = {
"Host":"music.163.com",
"Referer":"http://music.163.com/",
"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"}

def Find(pat,text):
	match = re.search(pat,text)
	if match == None:
		return ''
	#print(match.group(1))
	return match.group(1)
	
	
def getLyric2(idSong = "246316"):
	global lock,threads,hashLyricvisited,success,fail
	urlLyric = 'http://music.163.com/api/song/lyric?os=pc&id=' + idSong + '&lv=-1&kv=-1&tv=-1'
	try:
		r = requests.get(urlLyric,headers = headers,timeout = 1)
		text = r.text
		
		patLyric = '(?:"lyric":")(.+?)(?:")'
		lyric = Find(patLyric,text)
		# lyric = re.sub(r'\[.+?\]','',lyric)
		
		fileLyric = open(os.path.join('data_lyric',idSong+'.db'),'wb')
		fileLyric.write(lyric.encode('utf-8'))
		fileLyric.close()
		
		if lock.acquire():
			threads-=1
			hashLyricvisited[idSong] = True
			success+=1
			lock.release()
	except:
		if lock.acquire():
			threads-=1
			fail+=1
			lock.release()
#Initialization
if os.path.exists('lyric_visit.db'):
	hashLyricvisited = pickle.load(open('lyric_visit.db','rb'))
else:
	hashLyricvisited = {}
	
print('visited: ', len(hashLyricvisited))

f = open('song.db','r')
maxThreads = 100
threads = 0
lock = threading.Lock()
count = 1
last = time.time()
alpha = 1
success = 0
fail = 0
beta = 1
for line in f:
	id = line.strip('\n')
	while threads>=maxThreads:
		time.sleep(0.01)
	if hashLyricvisited.get(id,False)==False:
		if lock.acquire():
			threads+=1
			lock.release()
		time.sleep(0.01 + 0.1*(1-beta))
		threading.Thread(target=getLyric2,args=(id,)).start()
		count+=1
		if count%100==0:
			if time.time()-last < alpha:
				time.sleep(alpha-(time.time()-last))
			try:
				beta = float(success)/(success+fail+1)
				print("threads= ",threads,'\t',len(hashLyricvisited),'\t','time= %.2f'%(time.time()-last),'\t%.2f%%'%(beta*100))
				success = 0
				fail = 0
			except:
				pass
			last = time.time()
		if count>=2000:
			pickle.dump(hashLyricvisited,open('lyric_visit.db','wb'))
			print('-'*10+'pickled'+'-'*10)
			count-=2000
while True:
	time.sleep(0.5)
	if lock.acquire():
		if not threads:
			lock.release()
			break
		else:
			lock.release()
f.close()
fileLyric.close()