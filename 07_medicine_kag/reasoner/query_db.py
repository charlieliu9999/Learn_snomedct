import os
from knext.reasoner.client import ReasonerClient
from kag.common.conf import KAG_PROJECT_CONF

def query_database():
    """
    Query the database to check if data has been written.
    """
    resonser_path = os.path.dirname(os.path.abspath(__file__))
    project_path = os.path.dirname(resonser_path)
    host_addr = KAG_PROJECT_CONF.host_addr
    project_id = KAG_PROJECT_CONF.project_id
    namespace = KAG_PROJECT_CONF.namespace
    client = ReasonerClient(
        host_addr=host_addr, project_id=project_id, namespace=namespace
    )
    
    # Try different queries
    queries = [
        "MATCH (n) RETURN n LIMIT 5",
        "MATCH (n) RETURN labels(n) LIMIT 5",
        "MATCH (n) RETURN n.id LIMIT 5",
        "MATCH (n:Medicine02.HospitalDepartment) RETURN n.id LIMIT 5",
        "MATCH (n:HospitalDepartment) RETURN n.id LIMIT 5",
        "MATCH (n:`Medicine02.HospitalDepartment`) RETURN n.id LIMIT 5"
    ]
    
    for i, query in enumerate(queries):
        print(f"\nQuery {i+1}: {query}")
        try:
            result = client.execute(query)
            print("Result:")
            print(result)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    query_database()
