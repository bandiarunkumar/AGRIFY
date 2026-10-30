"""
Non-blocking startup validation
"""
import os

class StartupValidator:
    def validate(self):
        results = {}
        # Mandatory in production
        db_url = os.getenv('DATABASE_URL')
        results['database'] = 'CONFIGURED' if db_url and db_url.strip() else 'MISSING'
        
        jwt_secret = os.getenv('JWT_SECRET_KEY') or os.getenv('SECRET_KEY')
        results['jwt'] = 'CONFIGURED' if jwt_secret and len(jwt_secret.strip()) > 10 else 'MISSING'
        
        # Optional integrations
        results['weather'] = 'CONFIGURED' if os.getenv('OPENWEATHERMAP_API_KEY') and os.getenv('OPENWEATHERMAP_API_KEY').strip() else 'UNAVAILABLE'
        results['gemini'] = 'CONFIGURED' if os.getenv('GEMINI_API_KEY') and os.getenv('GEMINI_API_KEY').strip() else 'UNAVAILABLE'
        results['news'] = 'CONFIGURED' if os.getenv('NEWSAPI_KEY') and os.getenv('NEWSAPI_KEY').strip() else 'UNAVAILABLE'
        results['gemini_model'] = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        
        return results

validator = StartupValidator()
