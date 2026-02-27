## Episode 2: Refactor Your API with Type Hints and Pydantic

## 🎯 Objective

Now that your API is functional, refactor it to make full use of **Python type hints**, **`typing.Annotated`**, and **Pydantic**.

Watch the [**Mastering Python Type Hints**](https://youtu.be/q7GjjwnenZ4) video and apply the concepts to improve type safety, validation, and documentation across your codebase. Also start adding some structure and tests to your code as defined in sections 5 and 6 below.

Your goal is to clearly separate concerns between the API (delivery layer) and the inner layers of your app (use-cases and domain logic), while enforcing constraints consistently at runtime and in generated documentation. Outer layers should not interact directly with inner layers.

---

## 📋 Requirements

### 1\. Type Hints & Annotated Types

- Use Python type hints throughout the codebase.  
- Use `typing.Annotated` to describe:  
  - Field constraints (e.g. minimum and maximum values)  
  - Field descriptions (human-readable documentation)

### 2\. Pydantic Models & Validation

- Use **Pydantic models** for all Data Transfer Objects (DTOs) 
- Enforce the following constraints at runtime:  
  - `health` must be an integer between **1 and 100**  
  - `attributes` values must be integers between **1 and 100**  
- Validation must work both:  
  - When requests are sent through the API  
  - When domain logic is called directly (outside FastAPI)

### 3\. API Documentation

- The generated API documentation must:  
  - Display all field descriptions  
  - Display validation constraints (e.g. min/max values)
  - Display example schemas of what data you should send in / will receive
- Documentation should be automatically derived from type hints and `Annotated` metadata

### 4\. Data Transfer Objects (DTOs)

- Implement explicit DTOs using Pydantic to transfer data:  
  - From the Delivery Layer layer (`api.py`)  
  - Into the application logic (`application.py`)  
- DTOs should clearly define the boundary between delivery and inner layers

### 5\. Code Structure

Structure your code into these **source files**:

- **`api.py`**  
    
  - FastAPI application  
  - Route definitions  
  - Mapping to and from DTOs
  - FastAPI code should only exist here
  - Inner layers should not know about FastAPI

- **`domain.py`**  
    
  - Define domain types using Annotated Types
  - Domain models and value objects  
  - Domain object rules and invariants  
  - No FastAPI or CLI code

- **`application.py`**  
      
  - Application/use-case logic  
  - This code interacts with the domain models and value objects
  - Receives data from the api via DTO objects
  - Instantiates objects
  - Interacts with the repository
  - No FastAPI or CLI specific code

- **`dto.py`**  
    
  - Data Transfer Object definitions
  - No FastAPI, CLI code

- **`repository.py`**  
    
  - Any code which interacts with the json file
  - Retrieves and stores characters
  - No FastAPI or CLI code
  - No Application or Business Rules

### 6\. Add Some Tests

- Use pytest to add some tests

---

## ⭐ Bonus Challenge

- Create a **command-line interface (CLI)** that can interact directly with your domain logic using the same request and response DTOs 
- The CLI should interact with inner layers in a way similar to FastAPI 
- Keep the CLI as thin as possible and let the DTOs do the validation work for you

---

## 🧠 Learning Outcomes

By completing this quest, you will learn:

- How to protect your functions and data using Python type hints and Pydantic  
- How to use `Annotated` types to enrich models with constraints and metadata  
- How Pydantic absorbs information from `Annotated` types to enforce validation  
- How FastAPI generates OpenAPI documentation from type hints and annotations  
- How to design a clean boundary between API, DTOs, and domain logic  
- Why enforcing domain rules outside the web framework is critical for correctness
- Experiment with writing tests

---

## ✅ Success Criteria

- Invalid input is rejected both via the API and via direct domain calls  
- OpenAPI documentation clearly shows constraints and field descriptions  
- `api.py` contains no business rules / domain logic 
- Domain logic is reusable, testable, and framework-independent