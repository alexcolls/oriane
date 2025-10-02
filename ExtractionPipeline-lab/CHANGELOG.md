# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2025-07-07

### Added
- Initial CHANGELOG.md file
- Version bump to 1.2.0 following semantic versioning

### Changed
- Minor version bump from 1.1.0 to 1.2.0
- Updated API version in app.py

### Fixed
- Dependencies remain stable with no uuid or datetime extras needed (stdlib)

## [1.1.0] - Previous Release

### Added
- FastAPI service with visual search capabilities
- Video extraction pipeline with computer vision processing
- Qdrant vector database integration
- S3 upload/download functionality
- Authentication and security features
- Multi-platform support (Instagram, etc.)

### Dependencies
- Core dependencies frozen in requirements.txt files
- PyTorch 2.3.0+cu121 for CUDA 12.1 compatibility
- FastAPI, OpenCV, sentence-transformers, and other ML libraries
