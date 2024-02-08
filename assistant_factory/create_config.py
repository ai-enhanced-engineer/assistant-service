from commons.data_models.config import AssistantConfig
from commons.repositories.configs import GCPConfigRepository

CLIENT_ID = "nowisthetime"
BUCKET = "botbrewers"


def main():
    # Write config
    assistant_config = AssistantConfig(assistant_id="asst_Vu5GoPzaJpQFNcJkycx3CMks")
    config_repo = GCPConfigRepository(CLIENT_ID, BUCKET)
    config_repo.write_config(assistant_config)

    # Read config
    config = config_repo.read_config()
    print(config)


if __name__ == "__main__":
    main()
