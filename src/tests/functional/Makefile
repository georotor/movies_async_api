restart:
	docker-compose down -v && docker-compose up -dV --build
test:
	docker-compose restart tests && docker-compose logs -f tests
