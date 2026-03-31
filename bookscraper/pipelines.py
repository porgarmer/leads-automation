# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import re

class AbePipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item=item)
        
        author = adapter.get("author")
        
        if not author:
            raise DropItem("Missing author")
        
        author = self.clean_author(author=author)
        
        if not self.is_single_author(author=author):
            raise DropItem(f"Multip authors: {author}")
        
        if self.is_lname_fname(author=author):
            adapter["author"] = self.format_author_fname_lname(author=author)
        
        return item
    
    def clean_author(self, author):
        #remove trailing commas
        author = author.strip('"').strip()
        
        #remove anything after a quote
        author = author.split('"')[0]
        
        author = re.sub(r"\(.*?\)", "", author)
        
        return author.strip()
        
    def is_single_author(self, author):
        
        # obvous multi-author in
        if re.search(r"\b(and|with|et al)\b|[&;]", author.lower()):
            return False
        
        name_pattern = re.findall(r"[A-Za-z]+,\s*[A-Za-z]+", author)
        
        if len(name_pattern) > 1:
            return False
        
        words = author.split()
        capitalized = [w for w in words if w and w[0].isupper()]
        
        if len(capitalized) > 4:
            return False
        
        return True
    
    def is_lname_fname(self, author):
        if author.count(",") != 1:
            return False
            
        lname, fname = [p.strip() for p in author.split(",", 1)]
        
        if not lname or not fname:
            return False
            
        if len(fname.split()) > 3:
            return False
        
        return True
        
    def format_author_fname_lname(self, author):
        lname, fname = [p.strip() for p in author.split(",", 1)]
        return f"{fname} {lname}"
    
    