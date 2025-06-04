#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from neo4j import GraphDatabase

def test_connection():
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "neo4j@openspg"
    
    try:
        # 连接到Neo4j
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # 测试连接
        with driver.session() as session:
            result = session.run("RETURN 1 as num")
            record = result.single()
            if record and record["num"] == 1:
                print("Neo4j连接成功!")
            else:
                print("Neo4j连接测试失败，返回了意外的结果")
        
        # 关闭连接
        driver.close()
        return True
    except Exception as e:
        print(f"Neo4j连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
