import dlt

def test_dlt():
    pipeline = dlt.pipeline(pipeline_name="test_pl", destination="postgres", dataset_name="test_data")
    data = [{"id": 1, "nested": [{"name": "A"}]}, {"id": 2, "nested": [{"name": "B"}]}]
    load_info = pipeline.run(data, table_name="test_table")
    print("load_info:", load_info)
    
    # print all attributes
    print(dir(load_info))
    
    # to dict
    info_dict = load_info.asdict()
    print("keys in load_info dict:", info_dict.keys())
    
    # print tables
    print("Tables in pipeline:")
    for table_name in pipeline.default_schema.tables.keys():
        print("  -", table_name)

test_dlt()
