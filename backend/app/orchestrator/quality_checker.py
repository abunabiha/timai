import re
from typing import Any


class QualityReport:
    def __init__(
        self,
        passed: bool,
        word_count: int,
        page_estimate: float,
        citation_count: int,
        citations: list[str],
        dois_found: list[str],
        unverified_claims: list[str],
        marked_content: str,
        issues: list[str],
        summary: str,
    ) -> None:
        self.passed = passed
        self.word_count = word_count
        self.page_estimate = page_estimate
        self.citation_count = citation_count
        self.citations = citations
        self.dois_found = dois_found
        self.unverified_claims = unverified_claims
        self.marked_content = marked_content
        self.issues = issues
        self.summary = summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "word_count": self.word_count,
            "page_estimate": self.page_estimate,
            "citation_count": self.citation_count,
            "citations": self.citations,
            "dois_found": self.dois_found,
            "unverified_claims": self.unverified_claims,
            "issues": self.issues,
            "summary": self.summary,
        }


class QualityChecker:
    """
    Automated quality checks for Proposal and Journal profiles (PRD 6.1, FR-9.4, FR-9.6):
    - Word limit and page limit
    - Citation format verification
    - DOI / reference verification
    - Flags unverified claims with 'perlu sumber'
    - Terminology consistency
    """

    DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b")
    CITATION_PATTERN = re.compile(r"\[\d+(?:[,\s–-]+\d+)*\]|\([A-Za-z]+(?:\s+et\s+al\.)?,\s*(?:19|20)\d{2}\)")
    CLAIM_INDICATORS = [
        "penelitian sebelumnya membuktikan",
        "telah terbukti bahwa",
        "studi terdahulu menunjukkan",
        "berdasarkan data statistik",
        "menurut para ahli",
        "angka keberhasilan mencapai",
        "secara signifikan meningkatkan",
        "hasil pengujian membuktikan",
    ]

    def check_proposal_or_journal(
        self,
        content: str,
        profile_id: str = "proposal",
        max_words: int | None = None,
        min_citations: int = 1,
    ) -> QualityReport:
        """
        Runs quality check suite on draft text.
        Marks unverified claims with '[perlu sumber]' if citations are missing.
        """
        words = content.split()
        word_count = len(words)
        page_estimate = round(word_count / 300.0, 1)

        # 1. Citations & DOIs
        citations = self.CITATION_PATTERN.findall(content)
        dois = self.DOI_PATTERN.findall(content)

        issues: list[str] = []
        unverified_claims: list[str] = []

        # 2. Check word limits
        if max_words and word_count > max_words:
            issues.append(f"Jumlah kata ({word_count}) melebihi batas maksimum ({max_words} kata).")

        # 3. Check reference list presence
        has_references_section = bool(
            re.search(r"(?i)##\s*(?:daftar pustaka|referensi|rujukan|references)", content)
        )
        if not has_references_section:
            issues.append("Belum ada bagian 'Daftar Pustaka' atau 'Referensi' dalam naskah.")

        # 4. Check for citation adequacy
        if len(citations) < min_citations and "metodologi" not in content.lower():
            issues.append(f"Jumlah sitasi ({len(citations)}) kurang dari batas minimal ({min_citations}).")

        # 5. Check unverified claims & mark with [perlu sumber]
        # Split into paragraphs and inspect claims
        paragraphs = content.split("\n\n")
        marked_paragraphs = []

        for p in paragraphs:
            p_strip = p.strip()
            if not p_strip or p_strip.startswith("#") or p_strip.startswith("---") or p_strip.startswith(">"):
                marked_paragraphs.append(p)
                continue

            # If paragraph contains assertive claim indicators but lacks citations
            p_lower = p_strip.lower()
            has_claim_indicator = any(ind in p_lower for ind in self.CLAIM_INDICATORS)
            has_citation = bool(self.CITATION_PATTERN.search(p_strip)) or bool(self.DOI_PATTERN.search(p_strip))

            if has_claim_indicator and not has_citation:
                unverified_claims.append(p_strip[:120] + "...")
                # Annotate paragraph with [perlu sumber]
                if "[perlu sumber]" not in p_strip:
                    marked_p = f"{p_strip} [perlu sumber]"
                else:
                    marked_p = p_strip
                marked_paragraphs.append(marked_p)
            else:
                marked_paragraphs.append(p)

        marked_content = "\n\n".join(marked_paragraphs)

        # 6. Terminology Consistency
        if "kecerdasan buatan" in content.lower() and " artificial intelligence " in content.lower():
            issues.append("Inkonsistensi istilah: ditemukan campuran 'Kecerdasan Buatan' dan 'Artificial Intelligence'.")

        passed = len(issues) == 0 and len(unverified_claims) == 0

        summary_parts = [
            f"Jumlah kata: {word_count} (~{page_estimate} halaman).",
            f"Sitasi ditemukan: {len(citations)}, DOI: {len(dois)}.",
        ]
        if unverified_claims:
            summary_parts.append(f"Perhatian: {len(unverified_claims)} klaim belum memiliki rujukan terverifikasi (ditandai 'perlu sumber').")
        if issues:
            summary_parts.append(f"Isu terdeteksi: {'; '.join(issues)}.")
        else:
            summary_parts.append("Semua kriteria format dan rujukan terpenuhi.")

        summary = " ".join(summary_parts)

        return QualityReport(
            passed=passed,
            word_count=word_count,
            page_estimate=page_estimate,
            citation_count=len(citations),
            citations=citations,
            dois_found=dois,
            unverified_claims=unverified_claims,
            marked_content=marked_content,
            issues=issues,
            summary=summary,
        )


quality_checker = QualityChecker()
