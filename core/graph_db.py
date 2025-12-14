import json
from neo4j import GraphDatabase

# Kết nối đến Neo4j
URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "15102004")

driver = GraphDatabase.driver(URI, auth=AUTH)

# Đọc JSON chuẩn đã normalize


def import_report(tx, report):
    # Khóa duy nhất cho Report (công ty + loại + thời gian)
    report_id = f"{report['company']}|{report['type']}|{report['times']}"

    # Company
    tx.run("""
        MERGE (c:Company {name:$company})
    """, company=report["company"])

    # Sector
    tx.run("""
        MERGE (s:Sector {name:$sector})
    """, sector=report["sector"])

    # Liên kết Company -> Sector
    tx.run("""
        MATCH (c:Company {name:$company}), (s:Sector {name:$sector})
        MERGE (c)-[:BELONGS_TO]->(s)
    """, company=report["company"], sector=report["sector"])

    # Time
    tx.run("""
        MERGE (t:Time {value:$times})
    """, times=report["times"])

    # Report
    tx.run("""
        MERGE (r:Report {report_id:$report_id})
        SET r.type = $type, r.title = $type
        WITH r
        MATCH (c:Company {name:$company}), (t:Time {value:$times})
        MERGE (c)-[:HAS_REPORT]->(r)
        MERGE (r)-[:AT_TIME]->(t)
    """, report_id=report_id, company=report["company"], type=report["type"], times=report["times"])

    # Sections
    for sec in report["sections"]:
        section_id = f"{report_id}|{sec['title']}"
        tx.run("""
            MATCH (r:Report {report_id:$report_id})
            MERGE (s:Section {section_id:$section_id})
            SET s.title = $title,
                s.table_structure = $table_structure,
                s.raw_text = $raw_text,
                s.pages = $pages
            MERGE (r)-[:HAS_SECTION]->(s)
        """, report_id=report_id, section_id=section_id,
             title=sec["title"],
             table_structure=sec.get("table_structure"),
             pages = sec.get("pages"),
             raw_text=sec.get("raw_text"))  
        # Nếu có subsections thì tạo tiếp
        if "subsections" in sec:
            for sub in sec["subsections"]:
                subsection_id = f"{section_id}|{sub['subtitle']}"
                tx.run("""
                    MATCH (s:Section {section_id:$section_id})
                    MERGE (ss:Subsection {subsection_id:$subsection_id})
                    SET ss.subtitle = $subtitle,
                        ss.raw_text = $raw_text
                    MERGE (s)-[:HAS_SUBSECTION]->(ss)
                """, section_id=section_id, subsection_id=subsection_id,
                     subtitle=sub["subtitle"], raw_text=sub["raw_text"])

def add_new_report(data):
    # with open("graph_json/report_normalized.json", "r", encoding="utf-8") as f:
    #     data = json.load(f)

    report = data["report"]
    with driver.session(database='testreports') as session:
        session.execute_write(import_report, report)

    print("✅ Import JSON vào Neo4j thành công!")

# add_new_report()