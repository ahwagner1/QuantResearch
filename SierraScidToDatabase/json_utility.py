import os
import json



class JSONUtility:

    @classmethod
    def initialize_settings(cls) -> str:
        """
        This function creates the empty setting file for the individual commodities
        """
        settings_file = "./commodity_settings.json"

        if not os.path.exists(settings_file):
            settings_dict = {
                "symbol_settings" : {},
            }

            with open(settings_file, 'w') as f:
                json.dump(settings_dict, f, indent=4)
            
            print(f"Created JSON settings file: {settings_file}")
        
        return settings_file
    
    @classmethod
    def add_symbol_settings(cls, symbol) -> None:
        """
        This function adds a symbol to our json settings file with the params:
            "last_parsed_index"
            "initial_load_done" (may remove in future, probably redundant)
            "last_parsed_timestamp"
            "path_to_file"
        """
        with open("./commodity_settings.json", 'r') as f:
            settings = json.load(f)

        if symbol not in settings['symbol_settings']:
            settings['symbol_settings'][symbol] = {
                "last_parsed_index": 0,
                "initial_load_done": False,
                "last_parsed_timestamp": "",
                "path_to_file": f"C:/SierraChart/Data/{symbol}.scid",
            }
        
        with open("./commodity_settings.json", 'w') as f:
            json.dump(settings, f, indent=4)