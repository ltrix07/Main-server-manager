import json


def read_json(file_path: str):
    with open(file_path, 'r') as f:
        return json.load(f)


def collector_main_text_block(**kwargs) -> str:
    lines = [f"{key}: {value}" for key, value in kwargs.items()]
    text_block = '\n'.join(lines)

    return text_block


def collector_error_block(**kwargs) -> str:
    lines = [f"- {key}: {value}" for key, value in kwargs.items()]
    error_block = '\n'.join(lines)

    return error_block


def create_text_pattern(
        shop_name: str, text_block: str, error_block: str, amz_uploaded_status: bool, repricer_uploaded_status: bool
) -> str:
    repricer_text = 'Репрайсер успешно обновлен' if repricer_uploaded_status else 'Репрайсер не обновлен'
    amazon_text = 'Амазон успешно обновлен' if amz_uploaded_status else 'Амазон не обновлен'
    text = f'{shop_name}\n\n{text_block}\n\n{error_block}\n\n{amazon_text}\n{repricer_text}'

    return text
