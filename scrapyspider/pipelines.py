# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql.cursors
import sys
class ScrapyspiderPipeline(object):
    '''保存到数据库中对应的class
       1、在settings.py文件中配置
       2、在自己实现的爬虫类中yield item,会自动执行'''

    def __init__(self):
        self.dbparams = {
            'host':'127.0.0.1',
            'port': 3306,
            'user': 'root',
            'password': '1240',
            'db': 'scrapy_baike',
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
        }



    def execute_sql(self,sql):

        # 连接数据库，存到t中
        self.db = pymysql.connect(**self.dbparams)  # **表示将字典扩展为关键字参数,相当于host=xxx,db=yyy....
        self.cursor = self.db.cursor()

        try:
            self.cursor.execute('SET NAMES utf8mb4')
            self.cursor.execute("SET CHARACTER SET utf8mb4")
            self.cursor.execute("SET character_set_connection=utf8mb4")
            # 执行sql语句
            self.cursor.execute(sql)
            # 提交到数据库执行
            self.db.commit()
        except:
            # 如果发生错误则回滚
            print("ERR in sql execution!!; The sql is {}".format(sql))
            self.db.rollback()
            sys.exit(233)

        # 关闭数据库连接
        self.db.close()
        return self.cursor.rowcount

    def deal_with_quotes(self,processed_str):#处理插入MySQL的引号问题
        return processed_str.replace("\"","\\\"").replace("\'","\\\'")

    def create_entity_table(self,table_name):#datas is a dictionary
        sql="""
        CREATE TABLE %s(
        id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        oid         TEXT NOT NULL,
        name        TEXT NOT NULL,
        descrip     TEXT NOT NULL,
        infobox     TEXT,
        infolink   TEXT,
        tag         TEXT    
        );
        """%table_name
        self.execute_sql(sql)

        sql_db="""
        ALTER DATABASE %s CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
        """%self.dbparams['db']
        self.execute_sql(sql_db)

    def create_polysemant_table(self,table_name,):
        sql="""
        CREATE TABLE %s(
        id      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        name    TEXT NOT NULL,
        descrip TEXT NOT NULL,
        oid     TEXT NOT NULL
        );
        """%table_name
        self.execute_sql(sql)

    def exists_in_table(self,table_name,attribute_name,value_name):
        sql="""
        SELECT * FROM 
        %s
        WHERE %s="%s" ;
        """%(table_name,attribute_name,self.deal_with_quotes(value_name))
        if self.execute_sql(sql)==0:
            return False
        else:
            return True

    def add_a_value(self,table_name,attributes):
        count=0
        names=""
        values=""
        firstRun=True

        try:
            for name,value in attributes.items():
                name=str(name)
                value=str(value)
                if count>=len(attributes):
                    break

                if firstRun is False:
                    names="%s,%s"%(names,name)
                    values="%s,\"%s\""%(values,self.deal_with_quotes(value))
                else:
                    names="%s"%name
                    values="\"%s\""%self.deal_with_quotes(value)
                    firstRun=False
                count+=1
        except:
            sys.exit(104)

        sql = """
        INSERT INTO %s(%s)
        VALUES
        (%s);
       """ % (table_name, names, values.replace("\\\\\"","\\\""))
        self.execute_sql(sql)




    # pipeline默认调用
    def process_item(self, item, spider):
        data_dict=dict(item)

        self.entity_tbl_name='entity_table'
        entity_data_types=['oid','name','descrip','infobox','infolink','tag']
        entity_data_dict={}
        for t in entity_data_types:
            entity_data_dict[t]=data_dict[t]
        if self.exists_in_table(self.entity_tbl_name,'oid',data_dict['oid']) is False:
            self.add_a_value(self.entity_tbl_name,entity_data_dict)
        else:
            print('Warning: This item already exists in entity_table !! (checked by oid)')

        self.synonym_tbl_name='synonym_table'
        if self.exists_in_table(self.synonym_tbl_name,'name',data_dict['name']) is True:
            print('这个意思的同义词已经存入')
        else:
            polysemants_dict=data_dict['polysemy']
            for meaning, oid in polysemants_dict.items():
                if self.exists_in_table(self.synonym_tbl_name,'oid',oid) is False:
                    self.add_a_value(self.synonym_tbl_name,{'name':data_dict['name'],'descrip':meaning,'oid':oid})
                else:
                    print('Warning: the meaning/oid already exists in ')

        return item

