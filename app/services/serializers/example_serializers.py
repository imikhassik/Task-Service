from ...schemas.example_schemas import ProjectRegistryObject, ProjectModel, ProfileModel



def serialize_registry_entry_to_project_model(data: dict) -> ProjectModel | None:
    try:
        data = ProjectRegistryObject(**data)
    except Exception as e:
        print(f"Serialization error in method serialize_registry_entry_to_project_model, "
              f"schema ProjectRegistryObject.\n"
              f"Exception type: {type(e).__name__}\nMessage: {str(e)}\n"
              f"Object: {data}")
    output_data = {
        "project_id": data.id,
        "project_type": data.object_type,
        "project_name": data.name,
        "message": data.data.message
    }
    try:
        output_model = ProjectModel(**output_data)
        return output_model
    except Exception as e:
        print(f"Serialization error in method serialize_registry_entry_to_project_model, "
              f"schema ProjectModel.\n"
              f"Exception type: {type(e).__name__}\nMessage: {str(e)}\n"
              f"Object: {output_data}")



def serialize_profile_entry_to_profile_model(data: dict) -> ProfileModel | None:
    try:
        profile_model = ProfileModel(**data)
        return profile_model
    except Exception as e:
        print(f"Serialization error in method serialize_profile_entry_to_profile_model, "
              f"schema ProfileModel.\n"
              f"Exception type: {type(e).__name__}\nMessage: {str(e)}\n"
              f"Object: {data}")
