File: `receipes.py`

# TOOL CALL DEMO
```bash
└──$ python3 receipes.py
 Input> Can you tell me what's the weather in Patiala? Followed by that tell me what files are currently visible to you.
 Harness> Executing tools ...
 Harness> Executing tool: get_weather
 Harness> Executing tools ...
 Harness> Executing tool: list_directory
 LLM> The current weather in Patiala is 28 °C and sunny.
 Visible files in the root directory: `main.py`, `helpers.py`, `constants.py`.
 Input> Summarize what we have done till now.
 LLM> We fetched the current weather for Patiala (28 °C, sunny) using the weather API. Then we listed the root directory’s ontents, revealing three files: `main.py`, `helpers.py`, and `constants.py`. No other operations were performed.
 Input> quit
```
# COMPACTION DEMO
Prompts are given by an automated test, hence they may not make sense. They are just to test the compaction mechanism alongside toolcalls.

```bash
└──$ python3 receipes.py 
 ----
 Harness> Input Tok: 349, Cached Tok: 256
 Harness> Cache Hit
 ----
 LLM> Got it! Atlas uses Spring Boot, PostgreSQL, and Docker. I’ve noted those details for future reference. Let me know how I an help!
 ----
 Harness> Input Tok: 397, Cached Tok: 256
 Harness> Cache Hit
 ----
 Harness> Executing tools ...
 Harness> Executing tool: get_weather
 ----
 Harness> Input Tok: 464, Cached Tok: 256
 Harness> Cache Hit
 ----
 LLM> The current weather in Patiala is **Sunny** with a temperature of **28 °C**.
 ----
 Harness> Input Tok: 510, Cached Tok: 0
 Harness> No cached tokens reported.
 ----
 LLM> Got it—Atlas uses PostgreSQL.
 ----
 Harness> Input Tok: 537, Cached Tok: 0
 Harness> No cached tokens reported.
 ----
 Harness> Executing tools ...
 Harness> Executing tool: list_directory
 ----
 Harness> Input Tok: 606, Cached Tok: 256
 Harness> Cache Hit
 ----
 LLM> Contents of `/workspace/atlas`:
 - `main.py`
 - `helpers.py`
 - `constants.py`
 ----
 Harness> Input Tok: 658, Cached Tok: 256
 Harness> Cache Hit
 ----
 LLM> Understood—Atlas uses Flyway for database migrations.
 ----
 Harness> Input Tok: 695, Cached Tok: 0
 Harness> No cached tokens reported.
 ----
 LLM> - Project name: **Atlas**  
 - Database: **PostgreSQL**  
 - Migration tool: **Flyway**
 ----
 Harness> Input Tok: 751, Cached Tok: 256
 Harness> Cache Hit
 ----
 LLM> Got it—Orion is a separate project that uses **C++** and **gRPC**. It’s distinct from Atlas.
 ----
 Harness> Input Tok: 794, Cached Tok: 0
 Harness> No cached tokens reported.
 ----
 Harness> Executing tools ...
 Harness> Executing tool: get_weather
 ----
 Harness> Input Tok: 857, Cached Tok: 0
 Harness> No cached tokens reported.
 ----
 LLM> The current weather in Jaipur is **Sunny** with a temperature of **28 °C**.
 ----------------
 Harness> CONTEXT COMPACTED
 **Conversation Summary**
 | Topic | Key facts |
 |-------|-----------|
 | Project | **Atlas** |
 | Tech stack | Spring Boot, PostgreSQL, Docker |
 | Database migration tool | **Flyway** |
 | User preference | Concise answers |
 | Directory contents requested | `/workspace/atlas`: `main.py`, `helpers.py`, `constants.py` |
 | Weather request | Patiala – 28 °C, Sunny (obtained via `get_weather` tool) |
 No outstanding tasks remain. All decisions and preferences have been recorded.
 ----------------
 ----
 Harness> Input Tok: 621, Cached Tok: 0
 Harness> No cached tokens reported.
 ----
 LLM> ### Atlas (Spring Boot, PostgreSQL, Docker)
 | Decision | Rationale |
 |----------|-----------|
 | **Spring Boot** | Rapid microservice development, auto‑configuration, built‑in Actuator for monitoring |
 | **PostgreSQL** | Open‑source relational database, strong ACID support, good integration with Spring Data JPA |
 | **Flyway** | Versioned database migrations, easy rollback, integrates with Docker container start‑up |
 | **Docker** | Consistent runtime environment, containerized microservices, easy CI/CD |
 | **RESTful APIs** | Standard HTTP/JSON, aligns with Spring MVC, easy integration with front‑end |
 | **Project structure** | `src/main/java`, `src/main/resources`, `src/test/java` – standard Maven layout |
 | **Configuration** | `application.yml` for environment‑specific settings; externalized properties via Docker secrets or env ars |
 | **Testing** | JUnit 5 + Spring Test for unit/integration; Flyway checks in CI pipeline |
 ---
 ### Orion (C++ + gRPC)
 | Decision | Rationale |
 |----------|-----------|
 | **C++** | Performance‑critical components, fine‑grained control, large ecosystem for system‑level programming |
 | **gRPC** | High‑performance, type‑safe RPC with Protobuf, suitable for cross‑language communication |
 | **Protobuf** | Language‑agnostic IDL, auto‑generates stubs/clients, compact binary format |
 | **CMake** | Cross‑platform build system, integrates well with gRPC/Protobuf dependencies |
 | **Google Test** | Unit testing framework for C++, supports mock objects |
 | **Continuous Integration** | Build on Linux + Windows, run unit tests, generate coverage |
 | **Containerization** | Docker for consistent dev/production runtime, base image: `debian` or `alpine` + `g++` |
 | **Logging** | `spdlog` or `glog` for structured, leveled logging |
 | **Error handling** | Use `std::exception` hierarchy, wrap gRPC status codes into C++ exceptions for clarity |
 These choices keep Atlas and Orion focused on their respective technology stacks while ensuring maintainability, performance, nd easy deployment.
 ----
 Harness> Input Tok: 1110, Cached Tok: 0
 Harness> No cached tokens reported.
 ----
 LLM> The first location you asked about was **Patiala**.
 ----------------
 Harness> CONTEXT COMPACTED
 **Conversation Summary**
 | Topic | Key Facts |
 |-------|-----------|
 | Projects | - **Atlas**: Spring Boot, PostgreSQL, Docker, Flyway. <br> - **Orion**: C++, gRPC. (Clarified as distinct from tlas) |
 | User Preference | Concise responses. |
 | Weather | Jaipur: 28 °C, Sunny (retrieved via `get_weather` tool). |
 | Outstanding Tasks | None. All questions answered. |
 ---
 ----------------
```