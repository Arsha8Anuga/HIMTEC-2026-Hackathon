package service

import (
	"strings"
	"testing"
)

// F-09: every card has a source, a known category/aspect, a sane age range and only contract reason codes.
func TestGuidesDataIsWellFormed(t *testing.T) {
	s, err := New(nil, nil, "../../data")
	if err != nil {
		t.Fatal(err)
	}
	if len(s.Guides) == 0 {
		t.Fatal("guides.id.json kosong")
	}
	aspects := map[string]bool{"gerak_kasar": true, "gerak_halus": true, "bicara_bahasa": true, "sosialisasi_kemandirian": true}
	ids := map[string]bool{}
	for _, g := range s.Guides {
		if ids[g.ID] {
			t.Errorf("id ganda %s", g.ID)
		}
		ids[g.ID] = true
		if strings.TrimSpace(g.Title) == "" || strings.TrimSpace(g.Body) == "" || !strings.Contains(g.Source, "hlm.") {
			t.Errorf("%s: judul, isi, atau halaman sumber kosong", g.ID)
		}
		if g.AgeFromMonths < 0 || g.AgeToMonths > 60 || g.AgeFromMonths > g.AgeToMonths {
			t.Errorf("%s: rentang umur tidak valid", g.ID)
		}
		switch g.Category {
		case "mpasi":
			if g.Aspect != nil {
				t.Errorf("%s: kartu mpasi tidak punya aspek", g.ID)
			}
		case "stimulasi":
			if g.Aspect == nil || !aspects[*g.Aspect] {
				t.Errorf("%s: aspek stimulasi tidak dikenal", g.ID)
			}
		default:
			t.Errorf("%s: kategori %q", g.ID, g.Category)
		}
		if len(g.RelatedCodes) == 0 {
			t.Errorf("%s: related_codes kosong", g.ID)
		}
		for _, c := range g.RelatedCodes {
			if _, ok := s.Messages[c]; !ok {
				t.Errorf("%s: kode %s tidak ada di messages.id.json", g.ID, c)
			}
		}
	}
	// Every live KPSP form age (15, 18, 24) has a stimulation card for each aspect.
	for _, age := range []int{15, 18, 24} {
		a := age
		if n := len(s.FilterGuides("stimulasi", &a, "")); n != 4 {
			t.Errorf("umur %d: %d kartu stimulasi, harus 4", age, n)
		}
	}
}
