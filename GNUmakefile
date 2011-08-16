PYTHON?=`which python`
DESTDIR?=/
PROJECT=tema-tg
PROJECT_SETUP=tema-tg
BUILDIR=$(CURDIR)/debian/$(PROJECT)
DEBBUILD=debbuild
VERSION=3.2
RST2LATEXOPTS_SHORT=--use-latex-toc --use-latex-docinfo --documentoptions="a4paper,11pt" --hyperlink-color=black --graphicx-option=dvips
RST2LATEXOPTS_LONG=--use-part-section $(RST2LATEXOPTS_SHORT)
all:
	@echo "make source - Create source package"
	@echo "make apidoc - Create api documentation with epydoc"
	@echo "make htmldoc - README->README.html"
	@echo "make pdfdoc - README->README.pdf"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make builddeb - Generate a deb package"
	@echo "make buildwininst - Generate a windows installer"
	@echo "make clean - Get rid of scratch and byte files"

%.html: %
	rst2html $< > $@

%.tex: %
#	rst2latex --use-latex-toc --use-latex-docinfo --documentoptions="a4paper,11pt" --hyperlink-color=black --graphicx-option=dvips $< > $@
	rst2latex $(RST2LATEXOPTS_LONG)  $< > $@ || rst2latex $(RST2LATEXOPTS_SHORT)  $< > $@

%.pdf: %.ps
	ps2pdf $<

%.ps: %.dvi
	dvips $(basename $<)

%.dvi: %.tex
	latex $(basename $^)
	bibtex $(basename $^) || true
	( latex $(basename $^) | gawk '/Rerun/{rerun=1}{print $0}END{exit rerun}' ) || latex $(basename $^)


#%.pdf: %.tex
#	pdflatex $<

.PHONY: latexdocs
latexdocs:
	cd Docs/ssprotocol && $(MAKE) pdf
	cd Docs/testengine-for-developers && $(MAKE) pdf
#	cd Docs/userguide-unix && $(MAKE) pdf

.PHONY: htmldoc
htmldoc: README.html

.PHONY: pdfdoc
pdfdoc: README.pdf

.PHONY: apidoc
apidoc:
	cd TemaLib && epydoc --html --graph=all tema -o apidoc

.PHONY: source
source: clean latexdocs pdfdoc htmldoc
	$(PYTHON) setup.py sdist $(COMPILE)

.PHONY: buildrpm
buildrpm:
	$(PYTHON) setup.py bdist_rpm

.PHONY: buildwininst
buildwininst:
	$(PYTHON) setup.py bdist_wininst
	rename 's/$(PROJECT)-$(VERSION)(.*).exe/$(PROJECT)-$(VERSION).exe/g' dist/*.exe

.PHONY: builddeb
builddeb:
	# build the source package in the parent directory
	# then rename it to project_version.orig.tar.gz
	[ -d $(DEBBUILD) ] || mkdir $(DEBBUILD)
	rm -f MANIFEST
	$(PYTHON) setup.py sdist $(COMPILE) --dist-dir=$(DEBBUILD) --prune
	cd $(DEBBUILD) && tar xzf $(PROJECT_SETUP)-$(VERSION).tar.gz
	cd $(DEBBUILD)/$(PROJECT_SETUP)-$(VERSION) && dpkg-buildpackage -i -I -rfakeroot -us -uc
#	rename -f 's/$(PROJECT)-(.*)\.tar\.gz/$(PROJECT)_$$1\.orig\.tar\.gz/' ../*
	# build the package
#	dpkg-buildpackage -i -I -rfakeroot -us -uc

.PHONY: clean
clean:
	$(PYTHON) setup.py clean
	fakeroot $(MAKE) -f $(CURDIR)/debian/rules clean || true
	rm -rf build/ MANIFEST
	rm -rf apidoc
	find . -name '*.pyc' -delete
	find . -name '*~' -delete
	rm -f README.html
	rm -f README.pdf
	rm -f README.tex

distclean: clean
	rm -rf dist debbuild 