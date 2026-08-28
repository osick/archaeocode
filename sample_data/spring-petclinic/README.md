# Spring PetClinic — sample dataset

This directory contains a curated subset of the official
[Spring PetClinic](https://github.com/spring-projects/spring-petclinic) application
(Java sources, SQL schemas, and resources), bundled here as a **production-scale test
dataset** for archaeocode's Java analysis.

It is **third-party code**, © the original authors, redistributed under the
[Apache License 2.0](LICENSE). It is not part of archaeocode itself and is not meant
to be built or run from here — see the upstream repository for that.

Analyze it with:

```bash
python archaeo --source sample_data/spring-petclinic/src/main/java --source-lang java --target-lang python
```

Details about the curation and verified analysis results: [SAMPLE_INFO.md](SAMPLE_INFO.md).
