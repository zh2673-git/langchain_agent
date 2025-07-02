import sys
sys.path.append('/app')

try:
    from backend.api.openwebui_model_provider import get_openwebui_models
    import asyncio
    
    async def test():
        result = await get_openwebui_models()
        data = result.get('data', [])
        print(f'Models count: {len(data)}')
        
        for i, model in enumerate(data[:3]):
            model_id = model.get('id', '')
            model_name = model.get('name', '')
            print(f'{i+1}. {model_id} - {model_name}')
        
        return len(data)
    
    count = asyncio.run(test())
    print(f'Total: {count}')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
