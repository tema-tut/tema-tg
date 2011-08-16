# Copyright (c) 2006-2010 Tampere University of Technology
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

MAINTEX=$(firstword $(sort $(basename $(wildcard *.tex))))

.PHONY: help
help:
	@echo ""
	@echo "make pdf   - creates $(MAINTEX).pdf"
	@echo "make ps    - creates $(MAINTEX).ps"
	@echo "make clean - cleans up directory"
	@echo "make help  - shows this help"
	@echo ""

.PHONY: pdf
pdf:	$(MAINTEX).pdf

.PHONY: ps
ps:	$(MAINTEX).ps

%.pdf: %.ps
	ps2pdf $<

%.ps: %.dvi
	dvips $(basename $<)

%.dvi: %.tex $(wildcard *.tex)
	latex $(basename $^)
	bibtex $(basename $^) || true
	( latex $(basename $^) | gawk '/Rerun/{rerun=1}{print $0}END{exit rerun}' ) || latex $(basename $^)

.PHONY: clean
clean:
	$(RM) $(addprefix $(MAINTEX), .aux .log .dvi .pdf .ps .toc .bbl .blg) *~ */*~
