#!/usr/bin/env python
"""
Installing
	sudo apt install python-pip
	pip install requests
	pip install pymongo
"""

import datetime
import requests
from pymongo import MongoClient

mongodb = {
  "host": "localhost",
  "port": 27017,
  "database": "adeptio_statistics",
  "prefix": "stat_"
}

curl_url = {
  "getinfo.json": {
    "url":"https://explorer.adeptio.cc/api/getinfo",
    "param":{
    	"connections":"peer_online",
    	"blocks":"block_count",
    	"difficulty":"difficulty"
    }
  }, 
  "getmininginfo.json": {
    "url":"https://explorer.adeptio.cc/api/getmininginfo",
    "param":{
    	"networkhashps":"hashrate",
    	"blocks":"block_count",
    	"difficulty":"difficulty"
    }
  }, 
  "gettxoutsetinfo.json": {
    "url":"https://explorer.adeptio.cc/api/gettxoutsetinfo",
    "param":{
    	"total_amount":"coin_supply",
    	"transactions":"transaction_count",
    	"height":"block_count"
    }
  }, 
  "getmasternodecount.json": {
    "url":"https://explorer.adeptio.cc/api/getmasternodecount",
    "param":{
    	"masternodeCountOnline":"masternode_online",
    }
  }, 
  "summary.json": {
    "url":"https://explorer.adeptio.cc/ext/summary",
    "param":{
    	"blockcount":"block_count",
    	"supply":"coin_supply",
    	"connections":"peer_online",
    	"difficulty":"difficulty",
    	"masternodeCountOnline":"masternode_online",
    	"masternodeCountOffline":"masternode_offline",
    }
  }, 
  "crex24.json": {
    "url":"https://api.crex24.com/v2/public/tickers?instrument=ADE-BTC",
    "param":{
    	"last":{"key":"price","format":"{0:.8f}"},
    	"bid":{"key":"buy_price","format":"{0:.8f}"},
    	"ask":{"key":"sell_price","format":"{0:.8f}"},
    	"high":{"key":"24_highest_price","format":"{0:.8f}"},
    	"low":{"key":"24_lowest_price","format":"{0:.8f}"},
    	"volumeInBtc":"24_btc_volume",
    	"volumeInUsd":"24_usd_volume",
    	"baseVolume":"24_ade_volume"
    }
  }, 
}

class AdeptioStatistics():
  def __init__(self, mongodb):
    self.time = datetime.datetime.now()
    self.id = self.time.strftime("%Y_%m_%d")
    self.client = MongoClient(mongodb['host'], mongodb['port'])
    self.db = self.client[mongodb['database']]
    self.stat = self.db[mongodb['prefix']+self.id]

  def grep_data(self, data, param, r):
    for p in param:
      key = param[p]
      if isinstance(data, dict) and p in data:
        if isinstance(param[p], dict):
          key = param[p]['key']
          data[p] = param[p]['format'].format(float(data[p]))
        r[key] = data[p]
      elif data:
        r[key] = data
    return r

  def get_data(self, json):
    r = {}
    for file in json:
      f = json[file]
      pl = f['param']
      g = requests.get(f['url'])
      j = g.json()
      if isinstance(j, dict) and 'data' in j:
        j = j['data']
      if isinstance(j, list):
        j = j[0]
      if pl:
        r = self.grep_data(j,pl,r)
    return r

  def format_data(self, data):
  	t = self.time.strftime("%H:%M")
  	r = {}
  	for k in data:
  	  r[k+"."+t] = data[k]
  	return r

  def save_data(self, data):
  	if self.stat.count() <= 0:
  		self.stat.insert({'_id':self.id})
  	for d in data:
  		self.stat.update({'_id':self.id}, {"$set": data})

  def remove_same_data(self):
    stat = self.stat.find_one({'_id':self.id},{'_id':0})
    for key in stat:
      l = stat[key]
      if isinstance(l, dict):
        rem = {}
        bef = {}
        for t in sorted(l.iterkeys()):
          if bef.get(l[t]) and bef[l[t]] > 1:
            rem[key+"."+bef['t']] = 1
          bef = {l[t]:2,'t':t} if bef.get(l[t]) else {l[t]:1}
        if rem:
          self.stat.update({}, {'$unset': rem}, multi=True)

AS = AdeptioStatistics(mongodb)
data = AS.get_data(curl_url)
fdata = AS.format_data(data)
AS.save_data(fdata)
AS.remove_same_data()
