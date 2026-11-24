# 🛡️ GenTrust AI – AI Hallucination & Reliability Checker

### Verify AI-generated answers. Detect hallucinations. Build trust through evidence.

## 📌 Introduction

GenTrust AI is an AI-powered reliability assessment tool designed to identify incorrect, unsupported, or inconsistent information in AI-generated responses.

With the growing use of Generative AI, AI models can sometimes produce convincing answers that contain false information, misleading facts, or fabricated references. This is commonly known as **AI Hallucination**.

GenTrust AI helps address this problem by analysing AI-generated content, verifying factual claims using web evidence, checking answer consistency, and validating citations.

It generates an overall **Trust Score** along with detailed findings, verification results, and supporting sources to help users understand how reliable an AI-generated answer is.

## 🎯 Problem Statement

Generative AI models can generate answers that sound confident and accurate but may contain:
- Factually incorrect information.
- Fabricated statistics, dates, names, or events.
- Inconsistent answers to the same question.
- Fake or mismatched research papers, DOIs, and references.

Users often find it difficult to distinguish reliable AI-generated information from hallucinated content.

## 💡 Our Solution

GenTrust AI provides a multi-layered verification system that evaluates AI-generated answers through three major checks:

1. **Factual Verification** – Checks individual claims against available web evidence.
2. **Consistency Analysis** – Identifies contradictions when the AI model answers the same questions repeatedly.
3. **Citation Validation** – Checks whether references, research papers, DOIs, and links exist and match the provided information.

The results are combined into an overall reliability score with understandable explanations.

## ✨ Key Features

### 1. Factual Claim Verification
- Automatically extracts individual factual claims from an AI-generated answer.
- Searches the web for supporting or contradicting evidence.
- Uses DuckDuckGo search and Wikipedia as evidence sources.
- Prioritises recognised authoritative domains when ranking sources.
- Classifies each claim into three categories:
  - **Supported:** Evidence supports the claim.
  - **Contradicted:** Evidence conflicts with the claim.
  - **Unverifiable:** Available evidence is insufficient to confirm or refute the claim.

### 2. AI Consistency Testing
- Generates factual questions from the submitted answer.
- Asks the selected AI model the same questions multiple times.
- Compares the generated responses to identify factual differences.
- Detects inconsistencies involving names, dates, numbers, events, and explanations.
- Generates a consistency score from 0 to 100.

### 3. Citation & Reference Validation
- Detects DOIs, URLs, reference entries, and author-year citations.
- Checks DOI records using the Crossref API.
- Checks whether URLs are accessible.
- Identifies potentially fabricated DOIs.
- Detects cases where a real DOI is associated with a different research paper.
- Provides validation results for detected references.

### 4. Overall Trust Score
- Combines factual accuracy, consistency, and citation validation.
- Generates a score out of 100.
- Provides a human-readable reliability classification.
- Highlights important findings and potential risks.

### 5. Detailed Analysis Dashboard

The Streamlit dashboard provides different sections to explore the analysis:

- **Overview:** Overall trust score, reliability classification, and key findings.
- **Claims:** Individual factual claims with their verification verdicts and evidence.
- **Consistency:** Repeated answers, consistency scores, and identified contradictions.
- **Citations:** Reference validation results and associated information.
- **Export:** Download the final reliability report.

### 6. Customisable Analysis
- Choose the number of factual claims to verify.
- Enable or disable consistency testing.
- Configure the number of consistency questions.
- Enable or disable citation checking.
- Select from available Groq AI models or enter a custom model ID.
- Test the API connection before starting the analysis.

### 7. Report Export
- Download analysis reports in Markdown format.
- Download structured reports in JSON format.
- Access findings, scores, verification results, and supporting sources.

## ⚙️ How GenTrust AI Works

The application follows a multi-stage verification pipeline.

### Step 1: Input AI-Generated Content
The user pastes an AI-generated answer into the application or selects a sample example to test.

### Step 2: Factual Claim Extraction
The Groq-powered language model analyses the submitted content and separates it into smaller, independent, verifiable factual claims.

### Step 3: Evidence-Based Verification
Each extracted claim is searched using DuckDuckGo and Wikipedia. Retrieved evidence is ranked using source-quality indicators and passed to the AI model for evaluation.

Each claim receives one of three verdicts: Supported, Contradicted, or Unverifiable.

### Step 4: Consistency Analysis
The system generates factual questions from the submitted answer and asks the selected AI model to answer each question three times.

The responses are compared to identify factual contradictions and calculate a consistency score.

### Step 5: Citation Validation
The application identifies references, DOIs, and URLs in the submitted content.

It uses Crossref and URL accessibility checks to identify missing, inaccessible, or mismatched references.

### Step 6: Trust Score Calculation
The results from the available verification stages are combined using weighted scoring.

### Step 7: Final Reliability Report
The application presents an interactive dashboard containing the overall trust score, individual verification results, identified issues, and supporting evidence.

## 📊 Trust Score Calculation

The overall score combines three evaluation components:

| Evaluation Component | Weight |
|---|---:|
| Factual Accuracy | 60% |
| Consistency | 25% |
| Citation Validation | 15% |

**Scoring logic:**

- Supported claim = 1 point
- Unverifiable claim = 0.5 points
- Contradicted claim = 0 points

The weighted scores are combined to calculate the final reliability score. If a check is disabled or produces no scoreable result, the remaining component weights are proportionally adjusted.

### Reliability Classification

| Score | Classification |
|---|---|
| 85–100 | High Reliability |
| 70–84 | Generally Reliable |
| 50–69 | Use with Caution |
| Below 50 | Low Reliability |

If a claim is contradicted by evidence, the application does not classify the overall result as better than "Use with Caution", even if the numerical score is high.

**Important:** The trust score indicates how well the answer is supported by the implemented checks. It is not a mathematical probability that every statement is true.

## 🧰 Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic and processing |
| Streamlit | Interactive web application and dashboard |
| Groq API | AI-powered claim extraction, verification, and consistency analysis |
| DuckDuckGo Search | Retrieving web evidence |
| Wikipedia API | Additional factual evidence |
| Crossref API | Research paper and DOI validation |
| Requests | HTTP requests and URL accessibility checks |
| Python-dotenv | Secure API key configuration |

## 🖥️ How to Use

1. Launch GenTrust AI.
2. Configure your Groq API key.
3. Select the AI model you want to use.
4. Paste an AI-generated answer into the input area.
5. Configure the analysis options.
6. Click **Analyse Reliability**.
7. Wait for the verification pipeline to complete.
8. Explore the results through the Overview, Claims, Consistency, Citations, and Export sections.
9. Download the reliability report in Markdown or JSON format.

## 🔐 Security

- API keys are configured through environment variables.
- The `.env` file should never be uploaded to a public GitHub repository.
- Use `.env.example` to show other developers the required configuration.
- Keep credentials and other sensitive information out of source code.

## ⚠️ Limitations

- Verification depends on the availability and quality of retrieved web evidence.
- Search results may be incomplete or unavailable.
- A claim marked Unverifiable is not necessarily false.
- A valid DOI does not automatically prove that the cited paper supports the associated statement.
- Consistency between repeated AI responses does not guarantee factual correctness.
- The reliability score is an indicator based on automated checks and should not replace independent human verification.
- Groq API availability, model access, and rate limits may affect analysis.

## 🔮 Future Enhancements

- Support for analysing PDF and document uploads.
- Integration with additional trusted research databases and verification sources.
- Improved semantic comparison of factual claims.
- Browser extension for checking AI-generated answers directly on websites.
- Historical analysis and comparison of reliability reports.
- Support for multiple AI providers and cross-model verification.

## 🌍 Project Impact

GenTrust AI aims to encourage responsible and informed use of Generative AI by helping users identify potentially misleading information before relying on it.

It can be useful for students, researchers, educators, content creators, and professionals who regularly work with AI-generated information.

**Our Vision:** Make AI-generated information easier to question, verify, and trust through evidence-based evaluation.

---

**GenTrust AI – Don't just trust AI. Verify it.** 🛡️
