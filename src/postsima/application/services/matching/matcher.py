from postsima.application.models.matching import (
    MatchCandidate,
    MatchDecision,
    MatchEvidence,
    MatchFeature,
    MatchResult,
)
from postsima.application.services.matching.candidate_generator import (
    CandidateGenerator,
)
from postsima.application.services.matching.similarity import (
    coordinate_similarity,
    postal_code_similarity,
    text_similarity,
)
from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.entities.station import Station


class StationMatcher:
    MATCH_THRESHOLD = 0.80
    POSSIBLE_MATCH_THRESHOLD = 0.55

    def __init__(self, stations: list[Station]) -> None:
        self._candidate_generator = CandidateGenerator(stations)

    def match(self, record: SourceRecord) -> MatchResult:
        candidates = self._candidate_generator.find(record)

        scored: list[MatchCandidate] = []

        for station in candidates:
            candidate = self._score(record, station)

            if candidate is not None:
                scored.append(candidate)

        scored.sort(
            key=lambda candidate: candidate.score,
            reverse=True,
        )

        if not scored:
            return MatchResult(
                decision=MatchDecision.NO_MATCH,
            )

        best = scored[0]

        if best.score >= self.MATCH_THRESHOLD:
            return MatchResult(
                decision=MatchDecision.MATCH,
                station_id=best.station_id,
                candidates=tuple(scored),
                evidence=best.evidence,
            )

        if best.score >= self.POSSIBLE_MATCH_THRESHOLD:
            return MatchResult(
                decision=MatchDecision.POSSIBLE_MATCH,
                candidates=tuple(scored),
                evidence=best.evidence,
            )

        return MatchResult(
            decision=MatchDecision.NO_MATCH,
            candidates=tuple(scored),
        )

    def _score(
        self,
        record: SourceRecord,
        station: Station,
    ) -> MatchCandidate | None:
        scores: list[tuple[MatchFeature, float]] = []

        coordinate_score = coordinate_similarity(record, station)
        if coordinate_score is not None:
            scores.append(
                (MatchFeature.COORDINATES, coordinate_score)
            )

        name_score = text_similarity(
            record.name,
            station.name,
        )
        if name_score is not None:
            scores.append(
                (MatchFeature.NAME, name_score)
            )

        address_score = text_similarity(
            record.address,
            station.address,
        )
        if address_score is not None:
            scores.append(
                (MatchFeature.ADDRESS, address_score)
            )

        postal_score = postal_code_similarity(
            record,
            station,
        )
        if postal_score is not None:
            scores.append(
                (MatchFeature.POSTAL_CODE, postal_score)
            )

        if not scores:
            return None

        weighted_score = self._weighted_score(scores)

        evidence = tuple(
            MatchEvidence(
                feature=feature,
                description=f"Similarity: {score:.3f}",
                strength=score,
            )
            for feature, score in scores
        )

        return MatchCandidate(
            station_id=station.station_id,
            score=weighted_score,
            evidence=evidence,
        )

    @staticmethod
    def _weighted_score(
        scores: list[tuple[MatchFeature, float]],
    ) -> float:
        weights = {
            MatchFeature.COORDINATES: 0.85,
            MatchFeature.NAME: 0.05,
            MatchFeature.ADDRESS: 0.10,
            MatchFeature.POSTAL_CODE: 0.05,
        }

        total_weight = sum(
            weights[feature]
            for feature, _ in scores
        )

        if total_weight == 0:
            return 0.0

        return sum(
            weights[feature] * score
            for feature, score in scores
        ) / total_weight
