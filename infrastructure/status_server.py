"""
Status Server for Crypto Data Factory
Provides a real-time dashboard/API for system health
"""

import logging
from flask import Flask, jsonify
from threading import Thread

# Suppress Flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class StatusServer:
    """WebServer to display collector status"""
    
    def __init__(self, collectors, db, monitor, host='0.0.0.0', port=8080):
        self.collectors = collectors
        self.db = db
        self.monitor = monitor
        self.host = host
        self.port = port
        
        import os
        template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
        self.app = Flask(__name__, template_folder=template_dir)
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/')
        def index():
            # Serve the dashboard UI
            from flask import render_template
            return render_template('index.html')
            
        @self.app.route('/api/status')
        def status():
            # Basic system status
            return jsonify({
                "uptime": "running",
                "collectors_count": len(self.collectors),
                "db_connected": True if self.db else False,
                "field_stats": self.get_field_stats()
            })
            
        @self.app.route('/api/monitoring')
        def monitoring():
            # Detailed monitoring metrics
            if self.monitor:
                return jsonify(self.monitor.get_dashboard_data())
            return jsonify({"error": "Monitoring system not initialized"})
            
        @self.app.route('/api/errors')
        def errors():
            # Recent error logs
            if self.monitor:
                return jsonify(self.monitor.get_error_details(limit=50))
            return jsonify([])
            
        @self.app.route('/api/collectors')
        def collectors_status():
            status_data = {}
            for c in self.collectors:
                name = c.__class__.__name__
                try:
                    data = c.get_snapshot() if hasattr(c, 'get_snapshot') else {}
                    status_data[name] = {
                        "active": True,
                        "data_points": len(data)
                    }
                except Exception as e:
                    status_data[name] = {"error": str(e)}
            return jsonify(status_data)

    def get_field_stats(self):
        """Calculate field population statistics (simplified)"""
        if not self.db:
            return {}
        return {}  # Placeholder for DB stats logic to avoid blocking UI

    def run(self):
        """Start the Flask server"""
        print(f"🌍 Status Server starting on http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

    def shutdown(self):
        """Shutdown isn't natively supported by Flask/Werkzeug reliably in threads without obscure hacks."""
        pass
