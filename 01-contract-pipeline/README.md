# 01 - Contract Pipeline

Automated ingestion and normalization of federal contract data from SAM.gov and Department of Defense sources.

## Overview

This pipeline extracts contract award data, normalizes vendor and agency information, and loads it into a queryable data warehouse for downstream analysis.

## Data Sources

- **SAM.gov** - System for Award Management (federal contract opportunities and awards)
- **DoD contracts** - Department of Defense contract announcements

## Tech Stack

Python, SQL, PostgreSQL, Airflow, AWS (S3, Glue, Athena), Docker, Terraform

## Status

`Planned`
