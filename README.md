# OpenStreetMapDataWranglingWithMongoDB
This project illustrates some wrangling work done on Shanghai OpenStreeMap data. The data were first loaded into MongoDB, some simple requering was effected to have an overview of the data. Then a more detailed auditing of data quality was done with python, as well as the data wrangling and transformation. 

## Problems Encountered in the Map

### Encoding/decoding Chinese Characters

As I selected Shanghai_China.osm as my dataset, the first problem that I encountered is on the encoding/decoding of Chinese characters. 

- How to find Chinese characters in the value field and update them if necessary?
-	How to write them correctly into a JSON file?
-	Can Chinese characters be well imported into MongoDB?
-	How to pretty print human readable Chinese characters in the MongoDB requery results?

These were more of technical issues and I was struggling in treating them. 

To find Chinese characters, I used the regular expression ur'[\u4e00-\u9fff]+'. This expression may not be able to find all Chinese characters, for example, some rare traditional Chinese characters, but it allowed me to capture the majority of them. 

To write Chinese characters correctly into JSON file with Python 2, I used the io.open function with encoding parameter equal to “utf8”. And before writing into file, I first transform the data all in Unicode: **data = unicode(json.dumps(element, ensure_ascii=False))** with ensure_ascii deactivated in the json formating. 

MongoDB transform and store all data in Unicode format, so Chinese characters can be right interpreted and stored in MongoDB. But this will need extra encoding work when we retrieve them from MongoDB if we want display them in original human readable format.

To pretty print human readable Chinese characters, I defined my own PrettyPrinter class which overwrites the function format.

### Heterogeneous Name Value

I also noted that the value of name field was not uniformed. Many names were all written in Chinese while some were in English. And there was also a lot of names were a mix of Chinese and English. This increased considerably the difficulties of analyzing the dataset. 

In order to uniform the name format, idealIy, if the name was written in Chinese, the tag “name” should be updated to “name:zh”, and respectively “name:en” for the one written in English. And for those with Chinese and English mixed, I plan to split the name by retrieving the Chinese part and alphabetic part and put them into name:zh and name:en fields. 

However, it was not obvious to determine whether the Chinese characters and alphabetic letters presented in the name value were meaning the same name. For example, 

<tag k="name" v="浙江出版联合集团大楼Zhejiang publishing united group"/>
“浙江出版联合集团大楼” and “Zhejiang publishing united group” are Chinese name and English name of the same company. So it’s OK to split them into name:zh and name:en.

While for <tag k="name" v="闻涛路KFC"/>
“闻涛路” and “KFC” are not meaning the same thing.“闻涛路” stands for “Wen Tao Road” while KFC is a fast food restaurant. So the name can’t be splitted.

So it’s rather difficult to reshape and uniform the name value. And I didn’t find a good way to do it in my project.

Another problem concerning the name value was that many names were in reality meaning the same thing, but were written with extra descriptive information. For example, when I run following query to see top popular banks in Shanghai: 

> db.osm.aggregate([
        {"$match":{"amenity":{"$exists":1},"amenity":"bank"}},
  {"$group":{"_id":"$name.main", "count":{"$sum":1}}},
  {"$sort":{"count":¬-1}}])
 
 	 [{u'_id': u'中国银行', u'count': 30},
   	 {u'_id': u'工商银行', u'count': 25},
  	 {u'_id': u'农业银行', u'count': 15},
             {u'_id': u'建设银行', u'count': 14},
             {u'_id': u'中国建设银行', u'count': 14},
             {u'_id': u'招商银行', u'count': 13},
             {u'_id': u'中国工商银行', u'count': 13},
             {u'_id': u'中国农业银行', u'count': 11},
             {u'_id': u'ICBC', u'count': 9},
	     …
'工商银行', '中国工商银行' and 'ICBC' are all meaning “Industrial and Commercial Bank of China”, but they are counted as different banks. Similarly, '农业银行' (Agricultural Bank) and '中国农业银行' (Agricultural Bank of China) are in fact the same bank.

To solve this problem, we can use the same method as cleaning the street name, by giving an expected bank list written in Chinese, auditing the name and updating those who didn’t meet the list to the expected ones.  

### Address Issues

After auditing the addr:city, addr:street, addr:postcode, addr:housenumber fields, I noticed several problems.

**addr:city**

- Some cities were not Shanghai (ex. “Hangzhou”, “Wuxi”…) => ignore the tag
- Shanghai was written in different format (ex. “上海”, “上海市”, “Shanghai”…) => update the value to the expected one
- Some additional district information was presented (ex. “Huinanzhen, Pudong, Shanghai”) => remove additional information by setting the value to the expected one

**addr:street**

- Additional house number information was presented (ex. “NO.588 binhe road”, “浦建路207弄”…) => split the value by numbers, then depending on whether it’s written in Chinese or English, set the value to the good part (Chinese: set to the part before the housenumber, English: set to the part after the number)
- Some street types were written differently (ex. “Rd.”, “Rd”, “Road”, “road”…) => update the street types to expected ones

**addr:postcode**

- Some values were not valid postcode as Chinese postcode is composed of 6 numbers (ex. “20032”, “21351”, …) => ignore the tag
- Some values contained city information (ex. “201315 上海”…) => update the value to the number part
- Some values were not for Shanghai as Shanghai postcode starts always with “2” (ex. “312044”, “310014”…) => ignore the tag

**addr:housenumber**

- Many values were written in “Numbers-Numbers”, “Numbers;Numbers” and “Numbers～Numbers” formats (ex. “1366～1370”, “103;104” …) => update the value in format “Numbers;Numbers” and “Numbers～Numbers” to “Numbers-Numbers”
- Some values contained extra type information (ex. “26号”, “72弄”…) => extract the number and set it to the value
- Some values were not really house number (ex. “+8657584601405”, “U2cake”…) => ignore the tag
                      
## Overview of the data
                                                
This section contains basic statistics about the dataset and the MongoDB queries used to gather them.
                                                
- File size
                                                
shanghai_china.osm ......... 351 MB
shanghai_china.osm.json .... 396 MB

- Number of documents
                                                
>db.osm.find().count()  => 1905385

- Number of nodes
                                                
> db.osm.find({"type":"node"}).count()  => 1714276
                                                
- Number of ways
                                             
> db.osm.find({"type":"way"}).count()  => 191109

- Number of nodes or ways which have name
                                                
> db.osm.find({"name":{"$exists":1}}).count()  => 57550

- Number of nodes or ways which have English name
                                                
> db.osm.find({"name.en":{"$exists":1}}).count()  => 32324
                       
- Number of nodes or ways which have phone information
                                                
> db.osm.find({"phone":{"$exists":1}}).count()  => 63
                   
- Number of unique users
                                                
> db.osm.distinct("created.user").length  =>1198
                 
- Top 1 contributing user
> db.osm.aggregate([
{"$group":{"_id":"$created.user","count":{"$sum":1}}}, 
{"$sort":{"count":-¬1}}, 
{"$limit":1}])     

=> [{ "_id" : "XBear", "count" : 137007 }]                
                                                
## Other Ideas about the dataset

In order to improve the quality of data from Shanghai, I want to first explore where the OSM data come from. 

> db.osm.aggregate([
{"$match":{"created_by":{"$exists":1}}}, {"$group":{"_id":"$created_by","count":{"$sum":1}}}, {"$sort":{"count":¬ -1}},
{"$limit": 5}])

=> [{u'_id': u'almien_coastlines', u'count': 27195},
    {u'_id': u'JOSM', u'count': 6463},
    {u'_id': u'Potlatch 0.10f', u'count': 78},
    {u'_id': u'dkt_GNS-import-1', u'count': 69},
    {u'_id': u'Merkaartor 0.12', u'count': 57},
                
> db.osm.aggregate([
{"$match":{"source":{"$exists":1}}}, {"$group":{"_id":"$source","count":{"$sum":1}}}, {"$sort":{"count":¬ -1}},
{"$limit": 5}])

=> [{u'_id': u'PGS', u'count': 95347},
    {u'_id': u'Bing', u'count': 18452},
    {u'_id': u'bing', u'count': 5538},
    {u'_id': u'GPS', u'count': 5403},
    {u'_id': u'osm-gpx', u'count': 391}]}
  

From above two queries, it seems that most of the data are imported from PGS (Prototype Global Shoreline) coastline data by using the script “Almien coastlines”. However, according to the OSM wiki, the PGS data has in general an accuracy issue, as the data is based on Landsat (low resolution satellite imagery). In addition, the importing tool, Almien coastlines (PGS), is obsolete now. 

So I think we can go through two ways to improve the data of Shanghai:

**1)	Use better imagery to refine the accuracy**

I noticed there are only small amounts of data are created by GPS in Shanghai’s data. We can privilege the usage of on-the-ground GPS surveying or other techniques which produce better image as the main sources for the map.

**2)	Improve the importing script to clear the data, especially, handle the Chinese-English mixture issue of the name value.**

We can introduce the google translation service in the script. When the script found a Chinese-English mixed name, it will split the name into Chinese part and English part, do a request to google translation service to get the translation of the Chinese part, then compare with the stored English part to see if they match. If yes, the name can be logically reshaped to name:zh and name:en. 

However, there are two eventual disadvantages of this solution:

- Making requests to google translation service and waiting for the return to continue the work may greatly increase the process runtime. 

- We are not sure about the accuracy of the google translation service. It may give a very close but different translation to the expected English part, so make the script decision incorrect. In this case, we may need more intelligence (machine learning?) in the script to make wise decisions. 


