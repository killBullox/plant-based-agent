from social_agent.meta_client import MetaClient

c = MetaClient()
result = c.facebook_publish(
    message="🌱 Benvenuti su Beet It! Nutrizione vegetale che spacca. Senza sermoni, con energia. Stay tuned! #beetit #plantbased"
)
print(result)