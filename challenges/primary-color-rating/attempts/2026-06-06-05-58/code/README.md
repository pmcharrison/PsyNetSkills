# Primary color rating experiment

The runnable PsyNet experiment is in `primary_color_rating/`.

Run it locally with:

```bash
cd primary_color_rating
psynet test local
```

The implementation is nested one level down because PsyNet/Dallinger imports the
current directory by basename, and Python already has a standard-library module
named `code`.
