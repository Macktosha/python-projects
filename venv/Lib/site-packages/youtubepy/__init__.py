from urllib.request import urlopen
from urllib.parse import parse_qs
from urllib.parse import unquote
import urllib.request
import re
import pkgutil
import json
import datetime
import aiohttp
import asyncio

filter = pkgutil.get_data(__package__, 'safesearch.txt').decode('utf-8').replace("\r","").split("\n")

class BlockedWordError(Exception):
	"""A blocked word has been found in the video! Don't use safesearch filter if you want to ignore this error!"""
	
class VideoNotFoundError(Exception):
	""" No videos found with the given search query"""
	
class InvalidURL(Exception):
	"""The provided url is invalid!"""
	
async def geturl(self):
	async with aiohttp.ClientSession() as session:
		url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
		async with session.get(url) as resp:
			data = await resp.text()
			code = str(data)
			f = code.find('{"url":"/watch?v=')
			f += 9
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			self.url = url
	if "watch?v=" in url:
		return self.url
	else:
		Error = VideoNotFoundError("No videos found with the given search query")
		raise Error

async def getcode(self):
	async with aiohttp.ClientSession() as session:
		async with session.get(self.url) as resp:
			data = await resp.text()
			code = str(data)
			return code
		
async def down(url, filename):
	async with aiohttp.ClientSession() as session:
		async with session.get(url) as resp:
			content = await resp.read()
			with open(filename, "wb") as f:
				f.write(content)
				
async def getinfo(self):
	async with aiohttp.ClientSession() as session:
		async with session.get(f"https://www.youtube.com/get_video_info?video_id={self.id}&asv=3&el=detailpage&hl=en_US") as resp:
			info = await resp.read()
			info = info.decode("unicode_escape").encode("ascii","escape").decode("utf-8")
			info = parse_qs(info)
			return info
			
async def srcurl(info, self):
	keys = info["player_response"]
	source = None
	try:
		for dict in keys:
			dict = json.loads(dict)
			formats = dict["streamingData"]["formats"]
			codes = []
			for format in formats:
				codes.append(format["itag"])
			for format in formats:
				if format["itag"] == max(codes):
					source = format["url"]
					break
	except KeyError:
		import pafy
		source = pafy.new(self.url).getbest().url
	return source
	
async def audio(info, self):
	keys = info["player_response"]
	source = None
	try:
		for dict in keys:
			dict = json.loads(dict)
			formats = dict["streamingData"]["adaptiveFormats"]
			codes = []
			for format in formats:
				if "audioQuality" in format.keys():
					codes.append(format["itag"])
			for format in formats:
				if format["itag"] == max(codes):
					source = format["url"]
					break
	except KeyError:
		import pafy
		source = pafy.new(self.url).getbestaudio().url
	return source

class AsyncVideo:
	def __init__(self, query, **kwargs):
		self.safe = False
		if "safesearch" in kwargs.keys():
			self.safe = kwargs["safesearch"]
		self.query = query
		self.url = None
		self.data = None
		self.url = None
		self.source = None
		self.audio = None
		self.code = None
		self.info = None
		self.id = None
		self.nsfw = False
		self.video_title = None
		self.video_description = None
		self.likes = None
		self.dislikes = None
	async def search(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		if self.safe:
			if not self.code:
				self.code = await getcode(self)
			if not self.video_title:
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				titlee = re.search(titlepattern, self.code).group(1)
				self.video_title = titlee
			if not self.video_description:
				descpattern = '"shortDescription":"(.*?)","'
				description = str(re.search(descpattern, self.code).group(1))
				description = description.encode().decode('unicode_escape')
				description = description.replace("\\n","\n")
				self.video_description = description
			for word in filter:
				word = word.lower()
				title = self.video_title.lower()
				description = self.video_description.lower()
				if word in title or word in description or word in self.query.lower():
					self.nsfw = True
					break
				else:
					self.nsfw = False
		if self.safe:
			if self.nsfw:
				Error = BlockedWordError("A blocked word detected in the result video! Don't use safesearch to ignore this error!")
				raise Error
			else:
				return self.url
		else:
			return self.url
	async def title(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			lol, self.id = self.url.split("watch?v=")
		if not self.code:
			self.code = await getcode(self)
		if not self.video_title:
			titlepattern = '<meta itemprop="name" content="(.*?)">'
			titlee = re.search(titlepattern, self.code).group(1)
			self.video_title = titlee
		if self.safe:
			if not self.video_description:
				descpattern = '"shortDescription":"(.*?)","'
				description = str(re.search(descpattern, self.code).group(1))
				description = description.encode().decode('unicode_escape')
				description = description.replace("\\n","\n")
				self.video_description = description
			for word in filter:
				word = word.lower()
				title = self.video_title.lower()
				desc = self.video_description.lower()
				if word in title or word in desc or word in self.query:
					self.nsfw = True
					break
				else:
					self.nsfw = False
		if self.safe:
			if self.nsfw:
				Error = BlockedWordError("A blocked word detected in the result video! Don't use safesearch to ignore this error!")
				raise Error
			else:
				return self.video_title
		else:
			return self.video_title
	async def description(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		if not self.code:
			self.code = await getcode(self)
		if not self.video_description:
			descpattern = '"shortDescription":"(.*?)","'
			description = str(re.search(descpattern, self.code).group(1))
			description = description.encode().decode('unicode_escape')
			description = description.replace("\\n","\n")
			self.video_description = description
		if self.safe:
			if not self.video_title:
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				titlee = re.search(titlepattern, self.code).group(1)
				self.video_title = titlee
			for word in filter:
				word = word.lower()
				title = self.video_title.lower()
				desc = self.video_description.lower()
				if word in title or word in desc or word in self.query:
					self.nsfw = True
					break
				else:
					self.nsfw = False
		if self.safe:
			if self.nsfw:
				Error = BlockedWordError("A blocked word detected in the result video! Don't use safesearch to ignore this error!")
				raise Error
			else:
				return self.video_description
		else:
			return self.video_description
	async def channel_url(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.code:
			self.code = await getcode(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		channelurlpattern = '{"url":"/channel/(.*?)",'
		channel_url = re.search(channelurlpattern, self.code).group(1)
		channel_url = "https://www.youtube.com/channel/" + channel_url
		return channel_url
	async def thumbnail_url(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		thumb = "http://i.ytimg.com/vi/" + self.id + "/0.jpg"
		return thumb
	async def thumbnail_save(self, filename=None):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		thumb = "http://i.ytimg.com/vi/" + self.id + "/0.jpg"
		if not filename:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
				filename = self.video_title + ".jpg"
		try:
			await down(thumb, filename)
		except IsADirectoryError:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
			if filename.endswith("/"):
				filename = filename + self.video_title + ".jpg"
			else:
				filename = filename + "/" + self.video_title + ".jpg"
			await down(thumb, filename)
	async def duration(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		if not self.code:
			self.code = await getcode(self)
		durationpattern = '<meta itemprop="duration" content="(.*?)">'
		duration = re.search(durationpattern, self.code).group(1)
		mp = "PT(.*?)M"
		minutes = re.search(mp, duration).group(1)
		sp = f"PT{minutes}M(.*?)S"
		seconds = re.search(sp, duration).group(1)
		duration = []
		duration.append(str(seconds))
		duration.append(str(minutes))
		duration.append("0")
		if int(minutes) > 60:
			hours, mins = divmod(int(minutes), 60)
			duration[1] = mins
			duration[2] = hours
		if len(str(duration[0])) < 2:
			duration[0] = f"0{duration[0]}"
		if len(str(duration[1])) < 2:
			duration[1] = f"0{duration[1]}"
		if len(str(duration[2])) < 2:
			duration[2] = f"0{duration[2]}"
		duration = f"{duration[2]}:{duration[1]}:{duration[0]}"
		return duration
	async def view_count(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		if not self.code:
			self.code = await getcode(self)
		viewspattern = '{"viewCount":{"simpleText":"(.*?) views"}'
		views = re.search(viewspattern, self.code).group(1)
		return views
	async def like_count(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		if not self.code:
			self.code = await getcode(self)
		if not self.likes:
			likepattern = '{"label":"(.*?) likes"}}'
			likes = re.search(likepattern, self.code).group(1)
			self.likes = likes
		return self.likes
	async def dislike_count(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		if not self.code:
			self.code = await getcode(self)
		if not self.dislikes:
			dislikepattern = '{"accessibility":{"accessibilityData":{"label":"(.*?) dislikes"}}'
			dislikes = re.search(dislikepattern, self.code)
			dislikes = dislikes.group(1).split()
			dislikes = dislikes[len(dislikes)-1]
			dislikes= dislikes.split('"')
			dislikes = dislikes[len(dislikes)-1]
			self.dislikes = dislikes
		return self.dislikes
	async def average_rating(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		if not self.likes:
			if not self.code:
				self.code = await getcode(self)
			likepattern = '{"label":"(.*?) likes"}}'
			likes = re.search(likepattern, self.code).group(1)
			self.likes = likes
		if not self.dislikes:
			if not self.code:
				self.code = await getcode(self)
			dislikepattern = '{"accessibility":{"accessibilityData":{"label":"(.*?) dislikes"}}'
			dislikes = re.search(dislikepattern, self.code)
			dislikes = dislikes.group(1).split()
			dislikes = dislikes[len(dislikes)-1]
			dislikes= dislikes.split('"')
			dislikes = dislikes[len(dislikes)-1]
			self.dislikes = dislikes
		a = likes.split(",")
		a = likes.split(",")
		a = "".join(a)
		b = dislikes.split(",")
		b = "".join(b)
		likes = a
		dislikes = b
		x = float(self.likes) / 5
		y = float(self.dislikes) / x
		rating = 5 - y
		return rating
	async def channel_name(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.code:
			self.code = await getcode(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		channelnamepattern = '<link itemprop="name" content="(.*?)">'
		channel_name = re.search(channelnamepattern, self.code).group(1)
		return channel_name
	async def published_date(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		if not self.code:
			self.code = await getcode(self)
		datepattern = '"dateText":{"simpleText":"(.*?)"}}}'
		date = re.search(datepattern, self.code).group(1)
		return date
	async def source_url(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		if not self.info:
			self.info = await getinfo(self)
		if not self.source:
			self.source = await srcurl(self.info, self)
		if self.safe:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				titlee = re.search(titlepattern, self.code).group(1)
				self.video_title = titlee
			if not self.video_description:
				if not self.code:
					self.code = await getcode(self)
				descpattern = '"shortDescription":"(.*?)","'
				description = str(re.search(descpattern, self.code).group(1))
				description = description.encode().decode('unicode_escape')
				description = description.replace("\\n","\n")
				self.video_description = description
			for word in filter:
				title = self.video_title.lower()
				desc = self.video_description.lower()
				q = self.query.lower()
				if word in title or word in desc or word in q:
					self.nsfw = True
					break
				else:
					self.nsfw = False
		if self.safe:
			if self.nsfw:
				Error = BlockedWordError("A blocked word detected in the result video! Don't use safesearch to ignore this error!")
				raise Error
			else:
				return self.source
		else:
			return self.source
	async def audio_source(self):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		if not self.info:
			self.info = await getinfo(self)
		if not self.audio:
			self.audio = await audio(self.info, self)
		if self.safe:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				titlee = re.search(titlepattern, self.code).group(1)
				self.video_title = titlee
			if not self.video_description:
				if not self.code:
					self.code = await getcode(self)
				descpattern = '"shortDescription":"(.*?)","'
				description = str(re.search(descpattern, self.code).group(1))
				description = description.encode().decode('unicode_escape')
				description = description.replace("\\n","\n")
				self.video_description = description
			for word in filter:
				title = self.video_title.lower()
				desc = self.video_description.lower()
				q = self.query.lower()
				if word in title or word in desc or word in q:
					self.nsfw = True
					break
				else:
					self.nsfw = False
		if self.safe:
			if self.nsfw:
				Error = BlockedWordError("A blocked word detected in the result video! Don't use safesearch to ignore this error!")
				raise Error
			else:
				return self.audio
		else:
			return self.audio
	async def download(self, filename=None):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		if not self.source:
			if not self.info:
				self.info = await getinfo(self)
			self.source = await srcurl(self.info, self)
		if not filename:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
				filename = self.video_title + ".mp4"
		try:
			await down(self.source, filename)
		except IsADirectoryError:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
			if filename.endswith("/"):
				filename = filename + self.video_title + ".mp4"
			else:
				filename = filename + "/" + self.video_title + ".mp4"
			await down(self.source, filename)
	async def audio_download(self, filename=None):
		if not self.url:
			self.url = await geturl(self)
		if not self.id:
			x, self.id = self.url.split("watch?v=")
		if not self.audio:
			if not self.info:
				self.info = await getinfo(self)
			self.audio = await audio(self.info, self)
		if not filename:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
				filename = self.video_title + ".mp3"
		try:
			await down(self.audio, filename)
		except IsADirectoryError:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
			if filename.endswith("/"):
				filename = filename + self.video_title + ".mp3"
			else:
				filename = filename + "/" + self.video_title + ".mp3"
			await down(self.audio, filename)
			
class AsyncExtractData:
	def __init__(self, url):
		self.id = None
		if url.startswith("https://youtu.be"):
			x,y = url.split("youtu.be/")
			url = "https://www.youtube.com/watch?v=" + y
			self.id = y
		elif "watch?v=" in url:
			x,y = url.split("watch?v=")
			self.id = y
			url = "https://www.youtube.com/watch?v=" + y
		else:
			Error = InvalidURL("The provided url is invalid!")
			raise Error
		self.url = url
		self.source = None
		self.audio = None
		self.code = None
		self.info = None
		self.nsfw = False
		self.video_title = None
		self.video_description = None
		self.likes = None
		self.dislikes = None
	async def title(self):
		if not self.code:
			self.code = await getcode(self)
		if not self.video_title:
			titlepattern = '<meta itemprop="name" content="(.*?)">'
			titlee = re.search(titlepattern, self.code).group(1)
			self.video_title = titlee
		return self.video_title
	async def description(self):
		if not self.code:
			self.code = await getcode(self)
		if not self.video_description:
			descpattern = '"shortDescription":"(.*?)","'
			description = str(re.search(descpattern, self.code).group(1))
			description = description.encode().decode('unicode_escape')
			description = description.replace("\\n","\n")
			self.video_description = description
		return self.video_description
	async def channel_name(self):
		if not self.code:
			self.code = await getcode(self)
		channelnamepattern = '<link itemprop="name" content="(.*?)">'
		channel_name = re.search(channelnamepattern, self.code).group(1)
		return channel_name
	async def channel_url(self):
		if not self.code:
			self.code = await getcode(self)
		channelurlpattern = '{"url":"/channel/(.*?)",'
		channel_url = re.search(channelurlpattern, self.code).group(1)
		channel_url = "https://www.youtube.com/channel/" + channel_url
		return channel_url
	async def thumbnail_url(self):
		thumb = "http://i.ytimg.com/vi/" + self.id + "/0.jpg"
		return thumb
	async def thumbnail_save(self, filename=None):
		thumb = "http://i.ytimg.com/vi/" + self.id + "/0.jpg"
		if not filename:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
				filename = self.video_title + ".jpg"
		try:
			await down(thumb, filename)
		except IsADirectoryError:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
			if filename.endswith("/"):
				filename = filename + self.video_title + ".jpg"
			else:
				filename = filename + "/" + self.video_title + ".jpg"
			await down(thumb, filename)
	async def duration(self):
		if not self.code:
			self.code = await getcode(self)
		durationpattern = '<meta itemprop="duration" content="(.*?)">'
		duration = re.search(durationpattern, self.code).group(1)
		mp = "PT(.*?)M"
		minutes = re.search(mp, duration).group(1)
		sp = f"PT{minutes}M(.*?)S"
		seconds = re.search(sp, duration).group(1)
		duration = []
		duration.append(str(seconds))
		duration.append(str(minutes))
		duration.append("0")
		if int(minutes) > 60:
			hours, mins = divmod(int(minutes), 60)
			duration[1] = mins
			duration[2] = hours
		if len(str(duration[0])) < 2:
			duration[0] = f"0{duration[0]}"
		if len(str(duration[1])) < 2:
			duration[1] = f"0{duration[1]}"
		if len(str(duration[2])) < 2:
			duration[2] = f"0{duration[2]}"
		duration = f"{duration[2]}:{duration[1]}:{duration[0]}"
		return duration
	async def view_count(self):
		if not self.code:
			self.code = await getcode(self)
		viewspattern = '{"viewCount":{"simpleText":"(.*?) views"}'
		views = re.search(viewspattern, self.code).group(1)
		return views
	async def like_count(self):
		if not self.code:
			self.code = await getcode(self)
		if not self.likes:
			likepattern = '{"label":"(.*?) likes"}}'
			likes = re.search(likepattern, self.code).group(1)
			self.likes = likes
		return self.likes
	async def dislike_count(self):
		if not self.code:
			self.code = await getcode(self)
		if not self.dislikes:
			dislikepattern = '{"accessibility":{"accessibilityData":{"label":"(.*?) dislikes"}}'
			dislikes = re.search(dislikepattern, self.code)
			dislikes = dislikes.group(1).split()
			dislikes = dislikes[len(dislikes)-1]
			dislikes= dislikes.split('"')
			dislikes = dislikes[len(dislikes)-1]
			self.dislikes = dislikes
		return self.dislikes
	async def average_rating(self):
		if not self.likes:
			if not self.code:
				self.code = await getcode(self)
			likepattern = '{"label":"(.*?) likes"}}'
			likes = re.search(likepattern, self.code).group(1)
			self.likes = likes
		if not self.dislikes:
			if not self.code:
				self.code = await getcode(self)
			dislikepattern = '{"accessibility":{"accessibilityData":{"label":"(.*?) dislikes"}}'
			dislikes = re.search(dislikepattern, self.code)
			dislikes = dislikes.group(1).split()
			dislikes = dislikes[len(dislikes)-1]
			dislikes= dislikes.split('"')
			dislikes = dislikes[len(dislikes)-1]
			self.dislikes = dislikes
		a = self.likes.split(",")
		a = "".join(a)
		b = self.dislikes.split(",")
		b = "".join(b)
		likes = a
		dislikes = b
		x = float(likes) / 5
		y = float(dislikes) / x
		rating = 5 - y
		return rating
	async def published_date(self):
		if not self.code:
			self.code = await getcode(self)
		datepattern = '"dateText":{"simpleText":"(.*?)"}}}'
		date = re.search(datepattern, self.code).group(1)
		return date
	async def source_url(self):
		if not self.info:
			self.info = await getinfo(self)
		if not self.source:
			self.source = await srcurl(self.info, self)
		return self.source
	async def audio_source(self):
		if not self.info:
			self.info = await getinfo(self)
		if not self.audio:
			self.audio = await audio(self.info, self)
		return self.audio
	async def download(self):
		if not self.source:
			if not self.info:
				self.info = await getinfo(self)
			self.source = await srcurl(self.info, self)
		if not filename:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
				filename = self.video_title + ".mp4"
		try:
			await down(self.source, filename)
		except IsADirectoryError:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
			if filename.endswith("/"):
				filename = filename + self.video_title + ".mp4"
			else:
				filename = filename + "/" + self.video_title + ".mp4"
			await down(self.source, filename)
	async def audio_download(self):
		if not self.audio:
			if not self.info:
				self.info = await getinfo(self)
			self.audio = await audio(self.info, self)
		if not filename:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
				filename = self.video_title + ".mp3"
		try:
			await down(self.audio, filename)
		except IsADirectoryError:
			if not self.video_title:
				if not self.code:
					self.code = await getcode(self)
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
			if filename.endswith("/"):
				filename = filename + self.video_title + ".mp3"
			else:
				filename = filename + "/" + self.video_title + ".mp3"
			await down(self.audio, filename)
				
class Video:
	def __init__(self, query, **kwargs):
		self.safe = False
		self.quiet = False
		if "safesearch" in kwargs.keys():
			self.safe = kwargs["safesearch"]
		if "quiet" in kwargs.keys():
			self.quiet = kwargs["quiet"]
		self.query = query
		self.url = None
		self.data = None
		self.url = None
		self.source = None
		self.audio = None
		self.code = None
		self.info = None
		self.id = None
		self.nsfw = False
		self.video_title = None
		self.video_description = None
		self.likes = None
		self.dislikes = None
	def search(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find('{"url":"/watch?v=')
			f += 9
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			self.url = url
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if self.safe:
			if not self.code:
				html = urlopen(self.url)
				pagenonecode = html.read()
				code = str(pagenonecode)
				self.code = code
			if self.safe:
				global filter
				if not self.video_title:
					titlepattern = '<meta itemprop="name" content="(.*?)">'
					titlee = re.search(titlepattern, self.code).group(1)
					self.video_title = titlee
				if not self.video_description:
					descpattern = '"shortDescription":"(.*?)","'
					description = str(re.search(descpattern, self.code).group(1))
					description = description.encode().decode('unicode_escape')
					description = description.replace("\\n","\n")
					self.video_description = description
				for word in filter:
					word = word.lower()
					titlee = self.video_title.lower()
					desc = self.video_description.lower()
					query = self.query.lower()
					if word not in query and word not in titlee and word not in desc:
						self.nsfw = False
					else:
						self.nsfw = True
						break
			if self.safe:
				if self.nsfw:
					Error = BlockedWordError("A blocked word detected in the result video! Don't use safesearch to ignore this error!")
					raise Error
				else:
					if self.url != None and "watch?v=" in self.url:
						return self.url
					else:
						Error = VideoNotFoundError("No videos found with the given search query")
						raise Error
			else:
				if "watch?v=" in self.url:
					return self.url
				else:
					Error = VideoNotFoundError("No videos found with the given search query")
					raise Error
		else:
			if "watch?v=" in self.url:
				return self.url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
	def title(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		if not self.video_title:
			titlepattern = '<meta itemprop="name" content="(.*?)">'
			title = re.search(titlepattern, self.code).group(1)
			self.video_title = title
		if self.safe:
			if not self.video_description:
				descpattern = '"shortDescription":"(.*?)","'
				description = str(re.search(descpattern, self.code).group(1))
				description = description.encode().decode('unicode_escape')
				description = description.replace("\\n","\n")
				self.video_description = description
		if self.safe:
			global filter
			for word in filter:
				if word.lower() not in self.video_title.lower() and word.lower() not in self.video_description.lower() and word.lower() not in self.query.lower():
					self.nsfw = False
				else:
					self.nsfw = True
					break
		if self.safe:
			if self.nsfw:
				Error = BlockedWordError("A blocked word detected in the result video! Don't use safesearch to ignore this error!")
				raise Error
			else:
				if self.video_title != None:
					return self.video_title
		else:
			return self.video_title
	def channel_url(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		channelurlpattern = '{"url":"/channel/(.*?)",'
		channel_url = re.search(channelurlpattern, self.code).group(1)
		channel_url = "https://www.youtube.com/channel/" + channel_url
		return channel_url
	def thumbnail_url(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		x,keywords = self.url.split("watch?v=")
		thumb = "http://i.ytimg.com/vi/" + keywords + "/0.jpg"
		return thumb
	def thumbnail_save(self, filename=None):
		fetch = False
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		if not filename:
			titlepattern = '<meta itemprop="name" content="(.*?)">'
			title = re.search(titlepattern, self.code).group(1)
			filename = title + ".jpg"
		x,keywords = self.url.split("watch?v=")
		thumb = "http://i.ytimg.com/vi/" + keywords + "/0.jpg"
		try:
			urllib.request.urlretrieve(thumb, filename)
		except IsADirectoryError:
			titlepattern = '<meta itemprop="name" content="(.*?)">'
			title = re.search(titlepattern, self.code).group(1)
			if filename.endswith("/"):
				filename = filename + title + ".jpg"
			else:
				filename = filename + "/" + title + ".jpg"
			urllib.request.urlretrieve(thumb, filename)
	def duration(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		durationpattern = '<meta itemprop="duration" content="(.*?)">'
		duration = re.search(durationpattern, self.code).group(1)
		mp = "PT(.*?)M"
		minutes = re.search(mp, duration).group(1)
		sp = f"PT{minutes}M(.*?)S"
		seconds = re.search(sp, duration).group(1)
		duration = []
		duration.append(str(seconds))
		duration.append(str(minutes))
		duration.append("0")
		if int(minutes) > 60:
			hours, mins = divmod(int(minutes), 60)
			duration[1] = mins
			duration[2] = hours
		if len(str(duration[0])) < 2:
			duration[0] = f"0{duration[0]}"
		if len(str(duration[1])) < 2:
			duration[1] = f"0{duration[1]}"
		if len(str(duration[2])) < 2:
			duration[2] = f"0{duration[2]}"
		duration = f"{duration[2]}:{duration[1]}:{duration[0]}"
		return duration
	def view_count(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		viewspattern = '{"viewCount":{"simpleText":"(.*?) views"}'
		views = re.search(viewspattern, self.code).group(1)
		return views
	def like_count(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		likepattern = '{"label":"(.*?) likes"}}'
		likes = re.search(likepattern, self.code).group(1)
		if not self.likes:
			self.likes = likes
		return likes
	def dislike_count(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		dislikepattern = '{"accessibility":{"accessibilityData":{"label":"(.*?) dislikes"}}'
		dislikes = re.search(dislikepattern, self.code)
		dislikes = dislikes.group(1).split()
		dislikes = dislikes[len(dislikes)-1]
		dislikes= dislikes.split('"')
		dislikes = dislikes[len(dislikes)-1]
		if not self.dislikes:
			self.dislikes = dislikes
		return dislikes
	def average_rating(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		if not self.likes:
			likepattern = '{"label":"(.*?) likes"}}'
			likes = re.search(likepattern, self.code).group(1)
		if not self.dislikes:
			dislikepattern = '{"accessibility":{"accessibilityData":{"label":"(.*?) dislikes"}}'
			dislikes = re.search(dislikepattern, self.code)
			dislikes = dislikes.group(1).split()
			dislikes = dislikes[len(dislikes)-1]
			dislikes= dislikes.split('"')
			dislikes = dislikes[len(dislikes)-1]
		a = likes.split(",")
		a = likes.split(",")
		a = "".join(a)
		b = dislikes.split(",")
		b = "".join(b)
		likes = a
		dislikes = b
		x = float(likes) / 5
		y = float(dislikes) / x
		rating = 5 - y
		return rating
	def channel_name(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		channelnamepattern = '<link itemprop="name" content="(.*?)">'
		channel_name = re.search(channelnamepattern, self.code).group(1)
		return channel_name
	def description(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		if self.safe:
			if not self.video_title:
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
		if not self.video_description:
			descpattern = '"shortDescription":"(.*?)","'
			description = str(re.search(descpattern, self.code).group(1))
			description = description.encode().decode('unicode_escape')
			description = description.replace("\\n","\n")
			self.video_description = description
		if self.safe:
			global filter
			for word in filter:
				if word.lower() not in self.video_title.lower() and word.lower() not in self.video_description.lower() and word.lower() not in self.query.lower():
					self.nsfw = False
				else:
					self.nsfw = True
					break
		if self.safe:
			if self.nsfw:
				Error = BlockedWordError("A blocked word detected in the result video! Don't use safesearch to ignore this error!")
				raise Error
			else:
				if self.video_description != None:
					return self.video_description
		else:
			return self.video_description
	def published_date(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		datepattern = '"dateText":{"simpleText":"(.*?)"}}}'
		date = re.search(datepattern, self.code).group(1)
		return date
	def source_url(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		if not self.info:
			info = urlopen(f"https://www.youtube.com/get_video_info?video_id={self.id}&asv=3&el=detailpage&hl=en_US").read()
			info = info.decode("unicode_escape").encode("ascii","escape").decode("utf-8")
			info = parse_qs(info)
			self.info = info
		info = self.info
		keys = info["player_response"]
		source = None
		try:
			for dict in keys:
				dict = json.loads(dict)
				formats = dict["streamingData"]["formats"]
				codes = []
				for format in formats:
					codes.append(format["itag"])
				for format in formats:
					if format["itag"] == max(codes):
						source = format["url"]
						break
		except KeyError:
			import pafy
			source = pafy.new(self.url).getbest().url
		self.source = source
		if self.safe:
			if not self.video_title:
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
			if not self.video_description:
				descpattern = '"shortDescription":"(.*?)","'
				description = str(re.search(descpattern, self.code).group(1))
				description = description.encode().decode('unicode_escape')
				description = description.replace("\\n","\n")
				self.video_description = description
			global filter
			for word in filter:
				if word.lower() not in self.video_title.lower() and word.lower() not in self.video_description.lower() and word.lower() not in self.query.lower():
					self.nsfw = False
				else:
					self.nsfw = True
					break
		if self.safe:
			if self.nsfw:
				Error = BlockedWordError("A blocked word detected in the result video! Don't use safesearch to ignore this error!")
				raise Error
			else:
				if self.source != None:
					return self.source
		else:
			return self.source
	def audio_source(self):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		if not self.info:
			info = urlopen(f"https://www.youtube.com/get_video_info?video_id={self.id}&asv=3&el=detailpage&hl=en_US").read()
			info = info.decode("unicode_escape").encode("ascii","escape").decode("utf-8")
			info = parse_qs(info)
			self.info = info
		info = self.info
		keys = info["player_response"]
		source = None
		try:
			for dict in keys:
				dict = json.loads(dict)
				formats = dict["streamingData"]["adaptiveFormats"]
				codes = []
				for format in formats:
					if "audioQuality" in format.keys():
						codes.append(format["itag"])
				for format in formats:
					if format["itag"] == max(codes):
						source = format["url"]
						break
		except KeyError:
			import pafy
			source = pafy.new(self.url).getbestaudio().url
		self.audio = source
		if self.safe:
			if not self.video_title:
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
			if not self.video_description:
				descpattern = '"shortDescription":"(.*?)","'
				description = str(re.search(descpattern, self.code).group(1))
				description = description.encode().decode('unicode_escape')
				description = description.replace("\\n","\n")
				self.video_description = description
			global filter
			for word in filter:
				if word.lower() not in self.video_title.lower() and word.lower() not in self.video_description.lower() and word.lower() not in self.query.lower():
					self.nsfw = False
				else:
					self.nsfw = True
					break
		if self.safe:
			if self.nsfw:
				Error = BlockedWordError("A blocked word detected in the result video! Don't use safesearch to ignore this error!")
				raise Error
			else:
				if self.audio != None:
					return self.audio
		else:
			return self.audio
	def download(self, fp=None):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		if not self.info:
			info = urlopen(f"https://www.youtube.com/get_video_info?video_id={self.id}&asv=3&el=detailpage&hl=en_US").read()
			info = info.decode("unicode_escape").encode("ascii","escape").decode("utf-8")
			info = parse_qs(info)
			self.info = info
		info = self.info
		keys = info["player_response"]
		if not self.source:
			source = None
			try:
				for dict in keys:
					dict = json.loads(dict)
					formats = dict["streamingData"]["formats"]
					codes = []
					for format in formats:
						codes.append(format["itag"])
					for format in formats:
						if format["itag"] == max(codes):
							source = format["url"]
							break
			except KeyError:
				import pafy
				source = pafy.new(self.url).getbest().url
			self.source = source
		if not fp:
			if not self.video_title:
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
			fp = self.video_title + ".mp4"
		try:
			urllib.request.urlretrieve(self.source, fp)
		except IsADirectoryError:
			if fp.endswith("/"):
				fp = fp + self.video_title + ".mp4"
			else:
				fp = fp + "/" + self.video_title + ".mp4"
			urllib.request.urlretrieve(self.source, fp)
	def audio_download(self, fp=None):
		if not self.url:
			url = "https://www.youtube.com/results?search_query=" + self.query.replace(' ','+')
			html = urlopen(url)
			nonecode = html.read()
			code = str(nonecode)
			f = code.find("watch?v=")
			urllist = []
			urllist.append(code[f])
			cnt = 1
			while True:
				char = code[f+cnt]
				if char == '"':
					break
				else:
					urllist.append(char)
					cnt += 1
			url = "https://www.youtube.com/" + "".join(urllist)
			if "watch?v=" in url:
				self.url = url
			else:
				Error = VideoNotFoundError("No videos found with the given search query")
				raise Error
		if not self.id:
			x,y = self.url.split("watch?v=")
			self.id = y
		if not self.code:
			html = urlopen(self.url)
			pagenonecode = html.read()
			code = str(pagenonecode)
			self.code = code
		if not self.info:
			info = urlopen(f"https://www.youtube.com/get_video_info?video_id={self.id}&asv=3&el=detailpage&hl=en_US").read()
			info = info.decode("unicode_escape").encode("ascii","escape").decode("utf-8")
			info = parse_qs(info)
			self.info = info
		info = self.info
		keys = info["player_response"]
		if not self.audio:
			source = None
			try:
				for dict in keys:
					dict = json.loads(dict)
					formats = dict["streamingData"]["adaptiveFormats"]
					codes = []
					for format in formats:
						if "audioQuality" in format.keys():
							codes.append(format["itag"])
					for format in formats:
						if format["itag"] == max(codes):
							source = format["url"]
							break
			except KeyError:
				import pafy
				source = pafy.new(self.url).getbestaudio().url
		self.audio = source
		if not fp:
			if not self.video_title:
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
			fp = self.video_title + ".mp3"
		try:
			urllib.request.urlretrieve(self.audio, fp)
		except IsADirectoryError:
			if fp.endswith("/"):
				fp = fp + self.video_title + ".mp3"
			else:
				fp = fp + "/" + self.video_title + ".mp3"
			urllib.request.urlretrieve(self.audio, fp)
class ExtractData:
	def __init__(self, url):
		err = False
		try:
			if url.startswith("https://youtu.be"):
				x,y = url.split("https://youtu.be/")
				url = "https://www.youtube.com/watch?v=" + y
			x, self.id = url.split("www.youtube.com/watch?v=")
			self.url = url
		except:
			err = True
		if err:
			Error = InvalidURL("The provided url is invalid!")
			raise Error
		html = urlopen(url)
		nonecode = html.read()
		code = str(nonecode)
		self.code = code
		self.info = None
		self.source = None
		self.audio = None
		self.video_title = None
		self.likes = None
		self.dislikes = None
	def title(self):
		if not self.video_title:
			titlepattern = '<meta itemprop="name" content="(.*?)">'
			title = re.search(titlepattern, self.code).group(1)
			self.video_title = title
		return self.video_title
	def channel_url(self):
		channelurlpattern = '{"url":"/channel/(.*?)",'
		channel_url = re.search(channelurlpattern, self.code).group(1)
		channel_url = "https://www.youtube.com/channel/" + channel_url
		return url
	def thumbnail_url(self):
		x,keywords = self.url.split("watch?v=")
		thumb = "http://i.ytimg.com/vi/" + keywords + "/0.jpg"
		return thumb
	def thumbnail_save(self, filename=None):
		if not filename:
			titlepattern = '<meta itemprop="name" content="(.*?)">'
			title = re.search(titlepattern, self.code).group(1)
			filename = title + ".jpg"
		x,keywords = self.url.split("watch?v=")
		thumb = "http://i.ytimg.com/vi/" + keywords + "/0.jpg"
		try:
			urllib.request.urlretrieve(thumb, filename)
		except IsADirectoryError:
			titlepattern = '<meta itemprop="name" content="(.*?)">'
			title = re.search(titlepattern, self.code).group(1)
			if filename.endswith("/"):
				filename = filename + title + ".jpg"
			else:
				filename = filename + "/" + title + ".jpg"
			urllib.request.urlretrieve(thumb, filename)
	def duration(self):
		durationpattern = '<meta itemprop="duration" content="(.*?)">'
		duration = re.search(durationpattern, self.code).group(1)
		mp = "PT(.*?)M"
		minutes = re.search(mp, duration).group(1)
		sp = f"PT{minutes}M(.*?)S"
		seconds = re.search(sp, duration).group(1)
		duration = []
		duration.append(str(seconds))
		duration.append(str(minutes))
		duration.append("0")
		if int(minutes) > 60:
			hours, mins = divmod(int(minutes), 60)
			duration[1] = mins
			duration[2] = hours
		if len(str(duration[0])) < 2:
			duration[0] = f"0{duration[0]}"
		if len(str(duration[1])) < 2:
			duration[1] = f"0{duration[1]}"
		if len(str(duration[2])) < 2:
			duration[2] = f"0{duration[2]}"
		duration = f"{duration[2]}:{duration[1]}:{duration[0]}"
		return duration
	def view_count(self):
		viewspattern = '{"viewCount":{"simpleText":"(.*?) views"}'
		views = re.search(viewspattern, self.code).group(1)
		return views
	def like_count(self):
		likepattern = '{"label":"(.*?) likes"}}'
		likes = re.search(likepattern, self.code).group(1)
		self.likes = likes
		return likes
	def dislike_count(self):
		dislikepattern = '{"accessibility":{"accessibilityData":{"label":"(.*?) dislikes"}}'
		dislikes = re.search(dislikepattern, self.code)
		dislikes = dislikes.group(1).split()
		dislikes = dislikes[len(dislikes)-1]
		dislikes= dislikes.split('"')
		dislikes = dislikes[len(dislikes)-1]
		self.dislikes = dislikes
		return dislikes
	def average_rating(self):
		if not self.likes:
			likepattern = '{"label":"(.*?) likes"}}'
			likes = re.search(likepattern, self.code).group(1)
			self.likes = likes
		if not self.dislikes:
			dislikepattern = '{"accessibility":{"accessibilityData":{"label":"(.*?) dislikes"}}'
			dislikes = re.search(dislikepattern, self.code)
			dislikes = dislikes.group(1).split()
			dislikes = dislikes[len(dislikes)-1]
			dislikes= dislikes.split('"')
			dislikes = dislikes[len(dislikes)-1]
			self.dislikes = dislikes
		a = self.likes.split(",")
		a = "".join(a)
		b = self.dislikes.split(",")
		b = "".join(b)
		likes = a
		dislikes = b
		x = float(likes) / 5
		y = float(dislikes) / x
		rating = 5 - y
		return rating
	def channel_name(self):
		channelnamepattern = '<link itemprop="name" content="(.*?)">'
		channel_name = re.search(channelnamepattern, self.code).group(1)
		return channel_name
	def description(self):
		descpattern = '"shortDescription":"(.*?)","'
		description = str(re.search(descpattern, self.code).group(1))
		description = description.encode().decode('unicode_escape')
		description = str(description).replace("\\n","\n")
		return description
	def published_date(self):
		datepattern = '"dateText":{"simpleText":"(.*?)"}}}'
		date = re.search(datepattern, self.code).group(1)
		return date
	def source_url(self):
		if not self.info:
			info = urlopen(f"https://www.youtube.com/get_video_info?video_id={self.id}&asv=3&el=detailpage&hl=en_US").read()
			info = info.decode("unicode_escape").encode("ascii","escape").decode("utf-8")
			info = parse_qs(info)
			self.info = info
		info = self.info
		keys = info["player_response"]
		source = None
		try:
			for dict in keys:
				dict = json.loads(dict)
				formats = dict["streamingData"]["formats"]
				codes = []
				for format in formats:
					codes.append(format["itag"])
				for format in formats:
					if format["itag"] == max(codes):
						source = format["url"]
						self.source = source
						break
		except KeyError:
			import pafy
			source = pafy.new(self.url).getbest().url
			self.source = source
		return self.source
	def audio_source(self):
		if not self.info:
			info = urlopen(f"https://www.youtube.com/get_video_info?video_id={self.id}&asv=3&el=detailpage&hl=en_US").read()
			info = info.decode("unicode_escape").encode("ascii","escape").decode("utf-8")
			info = parse_qs(info)
			self.info = info
		info = self.info
		keys = info["player_response"]
		source = None
		try:
			for dict in keys:
				dict = json.loads(dict)
				formats = dict["streamingData"]["adaptiveFormats"]
				codes = []
				for format in formats:
					if "audioQuality" in format.keys():
						codes.append(format["itag"])
				for format in formats:
					if format["itag"] == max(codes):
						source = format["url"]
						self.source = source
						break
		except KeyError:
			import pafy
			source = pafy.new(self.url).getbestaudio().url
			self.source = source
		return self.source
	def download(self, fp=None):
		if not self.source:
			if not self.info:
				info = urlopen(f"https://www.youtube.com/get_video_info?video_id={self.id}&asv=3&el=detailpage&hl=en_US").read()
				info = info.decode("unicode_escape").encode("ascii","escape").decode("utf-8")
				info = parse_qs(info)
				self.info = info
		info = self.info
		keys = info["player_response"]
		if not self.source:
			source = None
			try:
				for dict in keys:
					dict = json.loads(dict)
					formats = dict["streamingData"]["formats"]
					codes = []
					for format in formats:
						codes.append(format["itag"])
					for format in formats:
						if format["itag"] == max(codes):
							source = format["url"]
							self.source = source
							break
			except KeyError:
				import pafy
				source = pafy.new(self.url).getbest().url
				self.source = source
		if not fp:
			if not self.video_title:
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
			fp = self.video_title + ".mp4"
		try:
			urllib.request.urlretrieve(self.source, fp)
		except IsADirectoryError:
			if fp.endswith("/"):
				fp = fp + self.video_title + ".mp4"
			else:
				fp = fp + "/" + self.video_title + ".mp4"
			urllib.request.urlretrieve(self.source, fp)
	def audio_download(self, fp=None):
		if not self.info:
			info = urlopen(f"https://www.youtube.com/get_video_info?video_id={self.id}&asv=3&el=detailpage&hl=en_US").read()
			info = info.decode("unicode_escape").encode("ascii","escape").decode("utf-8")
			info = parse_qs(info)
			self.info = info
		info = self.info
		keys = info["player_response"]
		if not self.audio:
			source = None
			try:
				for dict in keys:
					dict = json.loads(dict)
					formats = dict["streamingData"]["adaptiveFormats"]
					codes = []
					for format in formats:
						if "audioQuality" in format.keys():
							codes.append(format["itag"])
					for format in formats:
						if format["itag"] == max(codes):
							source = format["url"]
							self.audio = source
							break
			except KeyError:
				import pafy
				source = pafy.new(self.url).getbestaudio().url
				self.audio = source
		if not fp:
			if not self.video_title:
				titlepattern = '<meta itemprop="name" content="(.*?)">'
				title = re.search(titlepattern, self.code).group(1)
				self.video_title = title
			fp = self.video_title + ".mp3"
		try:
			urllib.request.urlretrieve(self.audio, fp)
		except IsADirectoryError:
			if fp.endswith("/"):
				fp = fp + self.video_title + ".mp3"
			else:
				fp = fp + "/" + self.video_title + ".mp3"
			urllib.request.urlretrieve(self.audio, fp)