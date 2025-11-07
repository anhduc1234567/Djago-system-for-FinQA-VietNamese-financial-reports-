from neo4j import GraphDatabase



URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "15102004")
driver = GraphDatabase.driver(URI, auth=AUTH)

def query_by_sector(sector = ''):
    query = """
    MATCH (c:Company)-[:BELONGS_TO]->(s:Sector {name:$sector_name})
    RETURN s.name AS sector, collect(c.name) AS companies
    """
    with driver.session() as session:
        result = session.run(query, sector_name=sector)
        records = [dict(record) for record in result]
    return records if records else None


def query_company_raw_text(company_name, time=None, section=None, subsection=None):
    with driver.session() as session:
        query = """
        MATCH (c:Company {name: $company_name})-[:HAS_REPORT]->(r:Report)
        """

        params = {"company_name": company_name}

        # Thêm bộ lọc thời gian (nếu có)
        if time:
            query += " -[:AT_TIME]->(t:Time {value: $time})"
            params["time"] = time
        else:
            query += " OPTIONAL MATCH (r)-[:AT_TIME]->(t:Time)"

        # Thêm section (nếu có)
        if section:
            query += " MATCH (r)-[:HAS_SECTION]->(s:Section {title: $section})"
            params["section"] = section
        else:
            query += " OPTIONAL MATCH (r)-[:HAS_SECTION]->(s:Section)"

        # Thêm subsection (nếu có)
        if subsection:
            query += " MATCH (s)-[:HAS_SUBSECTION]->(ss:Subsection {subtitle: $subsection})"
            params["subsection"] = subsection
        else:
            query += " OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(ss:Subsection)"

        query += """
        RETURN 
            c.name AS company,
            s.table_structure AS table_structure,
            s.pages AS pages,
            t.value AS time,
            COALESCE(ss.raw_text, s.raw_text, r.raw_text) AS raw_text
        """

        result = session.run(query, **params)
        return [record.data() for record in result]

def query_thuyet_minh_raw_text(company_name, time=None):
    """
    Hàm truy vấn phần 'THUYẾT MINH BÁO CÁO TÀI CHÍNH' của công ty tại thời điểm cụ thể.
    Nếu không có time thì sẽ lấy toàn bộ các kỳ báo cáo có phần thuyết minh.
    """
    with driver.session() as session:
        query = """
        MATCH (c:Company {name: $company_name})-[:HAS_REPORT]->(r:Report)
        """

        params = {"company_name": company_name}

        # Lọc theo thời gian nếu có
        if time:
            query += " -[:AT_TIME]->(t:Time {value: $time})"
            params["time"] = time
        else:
            query += " OPTIONAL MATCH (r)-[:AT_TIME]->(t:Time)"

        # Lọc theo phần thuyết minh
        query += """
        MATCH (r)-[:HAS_SECTION]->(s:Section {title: "THUYẾT MINH BÁO CÁO TÀI CHÍNH"})
        RETURN 
            c.name AS company,
            s.pages AS pages,
            t.value AS time,
            s.raw_text AS raw_text
        """

        result = session.run(query, **params)
        return [record.data() for record in result]
    
def query_gioi_thieu_raw_text(company_name, time=None):
    with driver.session() as session:
        query = """
        MATCH (c:Company {name: $company_name})-[:HAS_REPORT]->(r:Report)
        """

        params = {"company_name": company_name}

        # Lọc theo thời gian nếu có
        if time:
            query += " -[:AT_TIME]->(t:Time {value: $time})"
            params["time"] = time
        else:
            query += " OPTIONAL MATCH (r)-[:AT_TIME]->(t:Time)"

        # Lọc theo phần thuyết minh
        query += """
        MATCH (r)-[:HAS_SECTION]->(s:Section {title: "Giới thiệu"})
        RETURN 
            c.name AS company,
            s.pages AS pages,
            s.raw_text AS raw_text
        """

        result = session.run(query, **params)
        return [record.data() for record in result]
    
def query_raw_text(company_name, section, time=None):
    with driver.session() as session:
        query = """
        MATCH (c:Company {name: $company_name})-[:HAS_REPORT]->(r:Report)
        """

        params = {"company_name": company_name}

        if time:
            query += """
            MATCH (r)-[:AT_TIME]->(t:Time {value: $time})
            """
            params["time"] = time
        else:
            query += """
            OPTIONAL MATCH (r)-[:AT_TIME]->(t:Time)
            """

        query += """
        MATCH (r)-[:HAS_SECTION]->(s:Section {title: $section})
        WHERE NOT (s)-[:HAS_SUBSECTION]->()
        RETURN 
            c.name AS company,
            s.pages AS pages,
            t.value AS time,
            s.raw_text AS raw_text
        """

        params["section"] = section

        result = session.run(query, **params)
        return [record.data() for record in result]
# data = query_company_raw_text(
#     company_name="Công ty Cổ phần Tập đoàn Hòa Phát",
#     time="Bán niên 2025",
#     section="BẢNG CÂN ĐỐI KẾ TOÁN",
#     subsection="TÀI SẢN NGẮN HẠN"
# )

# for record in data:
#     print(record["table_structure"], ":", record["raw_text"])
