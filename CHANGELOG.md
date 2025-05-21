# CHANGELOG


## v1.3.1 (2025-05-21)

### Bug Fixes

- Fix .releaserc command
  ([`772fbd3`](https://github.com/Achaad/asar-xarray/commit/772fbd39fb89c553752bacc16537cb78ba70d565))

- Fix .releaserc command
  ([`8a038b4`](https://github.com/Achaad/asar-xarray/commit/8a038b43fc040f59d13304c1de3d690b3afe9976))

- Fix .releaserc command
  ([`3c2e0ef`](https://github.com/Achaad/asar-xarray/commit/3c2e0ef036fc4aabaddb9a32cfc706bfde88134c))

- Fix .releaserc command
  ([`b44342d`](https://github.com/Achaad/asar-xarray/commit/b44342d3a66d092fa85c890760c3d8d5343fca4b))

- Fix incorrect checkout depth
  ([`9af03e5`](https://github.com/Achaad/asar-xarray/commit/9af03e5e2af4ee1c8ad57a89f283d7f7791e427a))

- Update semantic release rules
  ([`efda9f7`](https://github.com/Achaad/asar-xarray/commit/efda9f7a68db86d780b5de1aa923090eb7388c78))

- Update semantic release rules
  ([`91c3aea`](https://github.com/Achaad/asar-xarray/commit/91c3aea5798cb43dd01abff2dfc485693cfd975e))

### Continuous Integration

- Pyproject.toml is updated based on new release
  ([#38](https://github.com/Achaad/asar-xarray/pull/38),
  [`8db35d8`](https://github.com/Achaad/asar-xarray/commit/8db35d88f22fbe25f3fed52092aeef011f20a83b))

Co-authored-by: Achaad <achaad@achaad.eu>


## v1.3.0 (2025-05-14)

### Build System

- Added loguru dependency for logging ([#34](https://github.com/Achaad/asar-xarray/pull/34),
  [`3ab44bf`](https://github.com/Achaad/asar-xarray/commit/3ab44bfae3c3020a916f2bbe03a78d2b31b50b3c))

### Chores

- **release**: Version 1.3.0 [skip ci]
  ([`76f0ed3`](https://github.com/Achaad/asar-xarray/commit/76f0ed35b21707c64f44624e1641a60da00d148e))

# [1.3.0](https://github.com/Achaad/asar-xarray/compare/v1.2.0...v1.3.0) (2025-05-14)

### Features

* add metadata parsing
  ([02357b3](https://github.com/Achaad/asar-xarray/commit/02357b3e2dd396f0bd5a5f2b6f736d53eaec89f0))

### Continuous Integration

- Configure type checking ([#33](https://github.com/Achaad/asar-xarray/pull/33),
  [`1d49d63`](https://github.com/Achaad/asar-xarray/commit/1d49d63af95c2801585b0e0bf728cf0230fa5cb8))

### Features

- Add metadata parsing
  ([`02357b3`](https://github.com/Achaad/asar-xarray/commit/02357b3e2dd396f0bd5a5f2b6f736d53eaec89f0))

### Testing

- Move test resource to some additional repository
  ([#32](https://github.com/Achaad/asar-xarray/pull/32),
  [`beb8f21`](https://github.com/Achaad/asar-xarray/commit/beb8f21edd2daeedbee2278a7e83c6151349d89a))

* make tests use external resources * Avoid usage of git lfs * Resources can be hosted anywhere


## v1.2.0 (2025-03-12)

### Chores

- **release**: Version 1.2.0 [skip ci]
  ([`5da1755`](https://github.com/Achaad/asar-xarray/commit/5da1755205f83607d1e5c81b5301978b9b5dfdc2))

# [1.2.0](https://github.com/Achaad/asar-xarray/compare/v1.1.0...v1.2.0) (2025-03-12)

### Features

* add initial support for opening ASAR files
  ([#24](https://github.com/Achaad/asar-xarray/issues/24))
  ([33a74c5](https://github.com/Achaad/asar-xarray/commit/33a74c55016226e5ab9b8d5711fe536e5f487d71))

### Continuous Integration

- Add coverage report support ([#16](https://github.com/Achaad/asar-xarray/pull/16),
  [`5d505bb`](https://github.com/Achaad/asar-xarray/commit/5d505bb71274d89621a3d8f3748bf58531dc5341))

- Add sonarqube analysis ([#13](https://github.com/Achaad/asar-xarray/pull/13),
  [`779e225`](https://github.com/Achaad/asar-xarray/commit/779e225a028495f3dea3a1da2bf322f23449db03))

- Add sonarqube pull request analysis ([#15](https://github.com/Achaad/asar-xarray/pull/15),
  [`416523c`](https://github.com/Achaad/asar-xarray/commit/416523c5ecb8b20069fe1cdc7f1733416811a9d0))

- Disable release action for pull requests
  ([`b586a1e`](https://github.com/Achaad/asar-xarray/commit/b586a1ed2d8c18f41821589b3b436a835df9daa4))

### Documentation

- Create general intro documentation ([#11](https://github.com/Achaad/asar-xarray/pull/11),
  [`3f47d2e`](https://github.com/Achaad/asar-xarray/commit/3f47d2e92435939a0afe6355ce739954024d7961))

* Update .gitignore with IntelliJ files

* Create initial documentation

### Features

- Add initial support for opening ASAR files ([#24](https://github.com/Achaad/asar-xarray/pull/24),
  [`33a74c5`](https://github.com/Achaad/asar-xarray/commit/33a74c55016226e5ab9b8d5711fe536e5f487d71))

* feat: add initial support for opening ASAR files

* Only pixel values are retrieved * No metadata parsing * NB! API is not final * Update CI to use
  conda environment * Update CI to support git lfs


## v1.1.0 (2025-03-04)

### Chores

- **release**: Version 1.1.0 [skip ci]
  ([`01482be`](https://github.com/Achaad/asar-xarray/commit/01482be227dc22eb4bde0ef6f6df1bbcdbe6e6b6))

# [1.1.0](https://github.com/Achaad/asar-xarray/compare/v1.0.1...v1.1.0) (2025-03-04)

### Features

* Create basic python module skeleton: ([#6](https://github.com/Achaad/asar-xarray/issues/6))
  ([#9](https://github.com/Achaad/asar-xarray/issues/9))
  ([601f969](https://github.com/Achaad/asar-xarray/commit/601f969b271f43bf14cf644422da25724e614051)),
  closes [#3](https://github.com/Achaad/asar-xarray/issues/3)

### Features

- Create basic python module skeleton: (#6) ([#9](https://github.com/Achaad/asar-xarray/pull/9),
  [`601f969`](https://github.com/Achaad/asar-xarray/commit/601f969b271f43bf14cf644422da25724e614051))

#3 Create basic python module skeleton: (#6)


## v1.0.1 (2025-03-04)

### Bug Fixes

- Additional permissions
  ([`fbabdef`](https://github.com/Achaad/asar-xarray/commit/fbabdef684feb1eca5709ddaf8768893e5bec3e5))

### Chores

- **release**: Version 1.0.1 [skip ci]
  ([`9a83ae0`](https://github.com/Achaad/asar-xarray/commit/9a83ae0d66098843e617d0a959a4ff5e2969417f))

## [1.0.1](https://github.com/Achaad/asar-xarray/compare/v1.0.0...v1.0.1) (2025-03-04)

### Bug Fixes

* additional permissions
  ([fbabdef](https://github.com/Achaad/asar-xarray/commit/fbabdef684feb1eca5709ddaf8768893e5bec3e5))


## v1.0.0 (2025-03-04)

### Bug Fixes

- Update action to allow write
  ([`3fc6069`](https://github.com/Achaad/asar-xarray/commit/3fc606962940389210b087329a47e75587017164))

- Wrong token
  ([`8290658`](https://github.com/Achaad/asar-xarray/commit/8290658b4f48f48bb88b3a4d819947af251b45aa))

### Chores

- **release**: Version 1.0.0 [skip ci]
  ([`1c3b970`](https://github.com/Achaad/asar-xarray/commit/1c3b9707918fcb6e2ad3601c6baf0b57bafcd6c3))

# 1.0.0 (2025-03-04)

### Bug Fixes

* update action to allow write
  ([3fc6069](https://github.com/Achaad/asar-xarray/commit/3fc606962940389210b087329a47e75587017164))
  * wrong token
  ([8290658](https://github.com/Achaad/asar-xarray/commit/8290658b4f48f48bb88b3a4d819947af251b45aa))

### Features

* add automatic semantic versioning ([#8](https://github.com/Achaad/asar-xarray/issues/8))
  ([8a203f6](https://github.com/Achaad/asar-xarray/commit/8a203f6e2ca27e30f5e67a8a67ea33c551373e60))

### Features

- Add automatic semantic versioning ([#8](https://github.com/Achaad/asar-xarray/pull/8),
  [`8a203f6`](https://github.com/Achaad/asar-xarray/commit/8a203f6e2ca27e30f5e67a8a67ea33c551373e60))

* Configure .releaserc file for versioning * Configure new github action
