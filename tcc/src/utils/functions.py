import tiktoken

global reference_prices
reference_prices = {
    "gpt-4": {"input": 0.03, "output":0.06},
    "gpt-4-turbo": {"input": 0.01, "output":0.03},
    "gpt-3.5-turbo": {"input": 0.0010, "output":0.0020},
    "gpt-3.5-turbo-instruct": {"input": 0.0015, "output":0.0020},
}

def num_tokens_from_string(string:str, llm_model:str) -> int:
    """Retorna o número de tokens aproximado dada uma string"""
    
    if 'gpt-4' in llm_model: llm_model = 'gpt-4'
    elif 'gpt-3.5' in llm_model: llm_model = 'gpt-3.5-turbo'
    
    encoding = tiktoken.encoding_for_model(llm_model)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def calculate_price(llm_model: str, text:str, mode:str="input") -> float:
    """Retorna o custo(USD) aproximado dada a conversão de uma string em tokens"""
     
    custo = reference_prices[llm_model][mode]
    price = num_tokens_from_string(text, llm_model)*custo/1000
    
    return price