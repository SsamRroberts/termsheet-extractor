# Blue Bridge Tech Assessment

## Getting Started

### Install
#### Prerequisites
1. [Docker compose](https://docs.docker.com/compose/install/)
2. Get an API key from [Synthetic](https://dev.synthetic.new/docs/api/models)
3. Environment variables, use `./backend/.env.example` as a template for your `.env`
#### Run
1. `docker compose up --build`

### Usage
1. Upload a PDF, view the extracted term sheet, hit approve to save.

### Test
1. `docker compose --profile test up test --build`