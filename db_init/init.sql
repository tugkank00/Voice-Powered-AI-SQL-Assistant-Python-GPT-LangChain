DROP TABLE IF EXISTS ai_service_usage;
DROP TABLE IF EXISTS ai_services;
DROP TABLE IF EXISTS ai_projects;

CREATE TABLE ai_services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL,
    input_price_per_1k_tokens DECIMAL(10, 5),
    output_price_per_1k_tokens DECIMAL(10, 5),
    supports_sql BOOLEAN,
    max_tokens INT,
    context_window VARCHAR(255),
    available BOOLEAN,
    launched_at DATE,
    description TEXT
);

CREATE TABLE ai_projects (
    id SERIAL PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    industry VARCHAR(255),
    country VARCHAR(255)
);

CREATE TABLE ai_service_usage (
    id SERIAL PRIMARY KEY,
    service_id INT NOT NULL,
    client_id INT NOT NULL,
    user_name VARCHAR(255),
    usage_date DATE,
    prompt_tokens INT,
    completion_tokens INT,
    FOREIGN KEY (service_id) REFERENCES ai_services(id),
    FOREIGN KEY (client_id) REFERENCES ai_projects(id)
);

INSERT INTO ai_services (name, provider, model, type, input_price_per_1k_tokens, output_price_per_1k_tokens, supports_sql, max_tokens, context_window, available, launched_at, description) VALUES
('ChatGPT 4 Turbo', 'OpenAI', 'gpt-4-turbo', 'chat', 0.0100, 0.0300, TRUE, 128000, '128k', TRUE, '2023-11-06', 'High-context GPT-4 Turbo model used for chat and SQL tasks'),
('Claude 3 Opus', 'Anthropic', 'claude-3-opus', 'chat', 0.0150, 0.0750, TRUE, 200000, '200k', TRUE, '2024-03-01', 'Claude 3 Opus with advanced reasoning'),
('Claude 3 Haiku', 'Anthropic', 'claude-3-haiku', 'chat', 0.0003, 0.0013, TRUE, 200000, '200k', TRUE, '2024-03-01', 'Fast and affordable Claude model'),
('Gemini 1.5 Pro', 'Google', 'gemini-1.5-pro', 'chat', 0.0050, 0.0150, TRUE, 1000000, '1M', TRUE, '2024-02-15', 'Massive context model from Google'),
('Mistral 7B Instruct', 'Local', 'mistral-7b-instruct', 'text-gen', 0.0000, 0.0000, FALSE, 32768, '32k', TRUE, '2023-10-01', 'Open source model for local inference'),
('GPT-3.5 Turbo', 'OpenAI', 'gpt-3.5-turbo', 'chat', 0.0005, 0.0015, TRUE, 16000, '16k', TRUE, '2022-11-30', 'Lightweight chat model for fast inference'),
('Claude 3.5 Sonnet', 'Anthropic', 'claude-3-5-sonnet', 'chat', 0.0020, 0.0060, TRUE, 200000, '200k', TRUE, '2024-08-15', 'Improved performance with better reasoning'),
('GPT-4o', 'OpenAI', 'gpt-4o', 'chat', 0.0050, 0.0150, TRUE, 128000, '128k', TRUE, '2024-05-13', 'Optimized multimodal model'),
('Gemini 1.5 Flash', 'Google', 'gemini-1.5-flash', 'chat', 0.0002, 0.0006, TRUE, 1000000, '1M', TRUE, '2024-04-10', 'Cost-effective Gemini variant'),
('Llama 3 70B', 'Meta', 'llama-3-70b', 'text-gen', 0.0000, 0.0000, FALSE, 128000, '128k', TRUE, '2024-04-18', 'Meta''s powerful open model');

INSERT INTO ai_projects (client_name, industry, country) VALUES
('TechNova', 'Healthcare', 'Germany'),
('AlphaFin', 'Finance', 'USA'),
('EduNext', 'Education', 'UK'),
('GreenTech', 'Renewable Energy', 'Canada'),
('DataCorp', 'Data Analytics', 'Australia');

INSERT INTO ai_service_usage (service_id, client_id, user_name, usage_date, prompt_tokens, completion_tokens) VALUES
(1, 1, 'alice', '2024-12-01', 1200, 3000),
(2, 2, 'bob', '2024-12-02', 1000, 2500),
(3, 3, 'carol', '2024-12-03', 800, 1800),
(4, 4, 'dave', '2024-12-04', 1500, 2100),
(5, 5, 'eve', '2024-12-05', 600, 1400),
(6, 1, 'frank', '2024-12-06', 900, 2200),
(7, 2, 'grace', '2024-12-07', 1100, 2700),
(8, 3, 'hank', '2024-12-08', 1300, 3100),
(9, 4, 'ivy', '2024-12-09', 700, 1600),
(10, 5, 'jack', '2024-12-10', 500, 1200);