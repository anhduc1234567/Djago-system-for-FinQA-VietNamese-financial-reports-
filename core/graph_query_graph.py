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

def query_company_raw_text(company_name, time=None, section=None, subsection=None, type_report=None):
    with driver.session() as session:
        query = """
        MATCH (c:Company {name: $company_name})-[:HAS_REPORT]->(r:Report)
        """
        params = {"company_name": company_name}

        # --- Lọc theo thời gian ---
        if time:
            query += """
            MATCH (r)-[:AT_TIME]->(t:Time {value: $time})
            """
            params["time"] = time
        else:
            query += """
            OPTIONAL MATCH (r)-[:AT_TIME]->(t:Time)
            """

        # --- Lọc theo loại báo cáo ---
        if type_report:
            query += """
            WHERE r.type = $type_report
            """
            params["type_report"] = type_report

        # --- Lọc theo section ---
        if section:
            query += """
            MATCH (r)-[:HAS_SECTION]->(s:Section {title: $section})
            """
            params["section"] = section
        else:
            query += """
            OPTIONAL MATCH (r)-[:HAS_SECTION]->(s:Section)
            """

        # --- Lọc theo subsection ---
        if subsection:
            query += """
            MATCH (s)-[:HAS_SUBSECTION]->(ss:Subsection {subtitle: $subsection})
            """
            params["subsection"] = subsection
        else:
            query += """
            OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(ss:Subsection)
            """

        # --- Trả kết quả ---
        query += """
        RETURN 
            c.name AS company,
            r.type AS report_type,
            s.table_structure AS table_structure,
            s.pages AS pages,
            t.value AS time,
            COALESCE(ss.raw_text, s.raw_text, r.raw_text) AS raw_text
        """

        result = session.run(query, **params)
        return [record.data() for record in result]


def query_thuyet_minh_raw_text(company_name, time=None, type_report=None):
    """
    Lấy phần 'THUYẾT MINH BÁO CÁO TÀI CHÍNH' của công ty.
    - Nếu time là None: lấy tất cả các kỳ.
    - Nếu type_report là None: lấy tất cả loại report.
    - Giữ nguyên logic gốc, chỉ thêm lọc theo r.type.
    """
    with driver.session() as session:
        query = """
        MATCH (c:Company {name: $company_name})-[:HAS_REPORT]->(r:Report)
        """
        params = {"company_name": company_name}

        # Lọc theo thời gian (nếu có)
        if time:
            query += """
            MATCH (r)-[:AT_TIME]->(t:Time {value: $time})
            """
            params["time"] = time
        else:
            query += """
            OPTIONAL MATCH (r)-[:AT_TIME]->(t:Time)
            """

        # Giữ nguyên phần logic ban đầu cho section
        query += """
        MATCH (r)-[:HAS_SECTION]->(s:Section {title: "THUYẾT MINH BÁO CÁO TÀI CHÍNH"})
        """

        # Thêm điều kiện lọc theo loại báo cáo (nếu có)
        if type_report:
            query += """
            WHERE r.type = $type_report
            """
            params["type_report"] = type_report

        # Trả về kết quả
        query += """
        RETURN 
            c.name AS company,
            r.type AS report_type,
            s.pages AS pages,
            t.value AS time,
            s.raw_text AS raw_text
        """

        result = session.run(query, **params)
        return [record.data() for record in result]
    
 
def query_raw_text(company_name, section, time=None, type_report=None):
    with driver.session() as session:
        query = """
        MATCH (c:Company {name: $company_name})-[:HAS_REPORT]->(r:Report)
        """
        params = {"company_name": company_name}

        # Nếu có thời gian cụ thể
        if time:
            query += """
            MATCH (r)-[:AT_TIME]->(t:Time {value: $time})
            """
            params["time"] = time
        else:
            query += """
            OPTIONAL MATCH (r)-[:AT_TIME]->(t:Time)
            """

        # Nếu có loại báo cáo cụ thể → lọc theo thuộc tính r.type
        if type_report:
            query += """
            WHERE r.type = $type_report
            """
            params["type_report"] = type_report

        # Lấy section
        query += """
        MATCH (r)-[:HAS_SECTION]->(s:Section {title: $section})
        WHERE NOT (s)-[:HAS_SUBSECTION]->()
        RETURN 
            c.name AS company,
            r.type AS report_type,
            s.pages AS pages,
            t.value AS time,
            s.raw_text AS raw_text
        """
        params["section"] = section

        result = session.run(query, **params)
        return [record.data() for record in result]
