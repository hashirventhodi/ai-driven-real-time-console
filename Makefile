.PHONY: run

run:
	uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
