import os

from knext.reasoner.client import ReasonerClient
from kag.common.conf import KAG_PROJECT_CONF


def read_dsl_files(directory):
    """
    Read all dsl files in the reasoner directory.
    """

    dsl_contents = []

    for filename in os.listdir(directory):
        if filename.endswith(".dsl"):
            file_path = os.path.join(directory, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                dsl_contents.append(content)

    return dsl_contents


if __name__ == "__main__":
    resonser_path = os.path.dirname(os.path.abspath(__file__))
    project_path = os.path.dirname(resonser_path)
    host_addr = KAG_PROJECT_CONF.host_addr
    project_id = KAG_PROJECT_CONF.project_id
    namespace = KAG_PROJECT_CONF.namespace
    client = ReasonerClient(
        host_addr=host_addr, project_id=project_id, namespace=namespace
    )
    print(f"Host address: {host_addr}")
    print(f"Project ID: {project_id}")
    print(f"Namespace: {namespace}")

    # Try a simple query directly
    try:
        print("\nTrying direct query: MATCH (n) RETURN n.id LIMIT 5")
        result = client.execute("MATCH (n) RETURN n.id LIMIT 5")
        print("Result:")
        print(result)
    except Exception as e:
        print(f"Error: {e}")

    # Read and execute DSL files
    dsls = read_dsl_files(resonser_path)
    print(f"\nFound {len(dsls)} DSL files")
    for i, dsl in enumerate(dsls):
        print(f"\nExecuting DSL {i+1}:")
        print(dsl)
        try:
            result = client.execute(dsl)
            print("Result:")
            print(result)
        except Exception as e:
            print(f"Error: {e}")
