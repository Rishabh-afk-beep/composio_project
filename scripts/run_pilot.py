import json
import httpx
import asyncio

async def run_pilot():
    with open('data/apps.json', 'r') as f:
        all_apps = json.load(f)

    # Pick a diverse set of 10 apps
    pilot_apps = [
        all_apps[0],  # Salesforce (CRM)
        all_apps[10], # Zendesk (Customer Support)
        all_apps[20], # Slack (Communication)
        all_apps[30], # Google Ads (Marketing)
        all_apps[40], # Shopify (Ecommerce)
        all_apps[50], # DataForSEO (SEO)
        all_apps[60], # GitHub (DevOps)
        all_apps[70], # Notion (Productivity)
        all_apps[80], # Stripe (Finance)
        all_apps[90]  # NotebookLM (AI)
    ]

    print(f"Starting pilot for {len(pilot_apps)} apps...")
    results = {}

    async with httpx.AsyncClient(timeout=300) as client:
        for app in pilot_apps:
            name = app['app_name']
            print(f"Researching: {name}...")
            try:
                # The backend handles Firecrawl, LLM, Composio checks
                r = await client.post(f"http://localhost:8000/research/{name}")
                if r.status_code == 200:
                    results[name] = r.json()
                    print(f"  -> SUCCESS ({results[name].get('score', 0)}/100)")
                else:
                    results[name] = {"error": f"HTTP {r.status_code}: {r.text}"}
                    print(f"  -> ERROR HTTP {r.status_code}")
            except Exception as e:
                results[name] = {"error": str(e)}
                print(f"  -> EXCEPTION: {e}")
            
            # Short delay between requests to avoid rate limits
            await asyncio.sleep(5)

    with open('data/pilot_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("Pilot complete! Saved to data/pilot_results.json")

if __name__ == "__main__":
    asyncio.run(run_pilot())
