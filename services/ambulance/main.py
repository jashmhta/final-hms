from templates.service_main import create_service_app, run_service
app = create_service_app(
    service_name="Ambulance",
    service_description="API for ambulance service in HMS Enterprise-Grade System",
    version="1.0.0"
)
if __name__ == "__main__":
    run_service(app, port=8000)