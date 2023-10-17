import requests
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from html import unescape
from xml.dom import minidom
import os

def main():
    feeds = [
        {
            'url': 'https://www.google.co.jp/alerts/feeds/04259142089098243371/517199022479736050',
            'xml': 'feed_GoogleAlert_Yumiki.xml',
            'include_phrase': ['弓木', '奈於'],
            'exclude_phrase': []
        },
        {
            'url': 'https://www.google.co.jp/alerts/feeds/04259142089098243371/4699800603100712327',
            'xml': 'feed_GoogleAlert_Kanagawa.xml',
            'include_phrase': ['金川', '紗耶'],
            'exclude_phrase': []
        }
    ]
    
    for feed in feeds:
        url = feed['url']
        xml_file = feed['xml']
        include_phrase = feed['include_phrase']
        exclude_phrase = feed['exclude_phrase']  # ここでexclude_phraseを追加したよ

        # 既存のRSSフィードを読む
        existing_links = set()
        if os.path.exists(xml_file):
            tree = ET.parse(xml_file)
            root = tree.getroot()
        else:
            root = ET.Element("rss", version="2.0")
            channel = ET.SubElement(root, "channel")
            ET.SubElement(channel, "title").text = "Google Alerts"
            ET.SubElement(channel, "description").text = "Google Alertsからの情報を提供します。"
            ET.SubElement(channel, "link").text = url

        for item in root.findall(".//item/link"):
            existing_links.add(item.text)
        
        # スクレイピング処理
        response = requests.get(url)
        html_content = unescape(response.text)

        article_pattern = re.compile(r'<entry[^>]*>([\s\S]*?)<\/entry>')

        for match in article_pattern.findall(html_content):
            title = re.search(r'<title[^>]*>(.*?)<\/title>', match).group(1)
            link = re.search(r'<link href="(.*?)"/>', match).group(1)
            date_str = re.search(r'<published>(.*?)<\/published>', match).group(1)
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%Y.%m.%d %H:%M")
            
            # タイトルのフィルタリング
            if any(phrase in title for phrase in include_phrase) and not any(phrase in title for phrase in exclude_phrase):
                
                if link in existing_links:
                    continue
                
                channel = root.find("channel")
                new_item = ET.SubElement(channel, "item")
                ET.SubElement(new_item, "title").text = title
                ET.SubElement(new_item, "link").text = link
                ET.SubElement(new_item, "pubDate").text = date

        # XMLを出力
        xml_str = ET.tostring(root)
        xml_pretty_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
        xml_pretty_str = os.linesep.join([s for s in xml_pretty_str.splitlines() if s.strip()])

        with open(xml_file, "w") as f:
            f.write(xml_pretty_str)

if __name__ == "__main__":
    main()
